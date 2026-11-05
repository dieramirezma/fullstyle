"""Server-priced intents and atomic settlement of signed synthetic provider events."""

import os
from datetime import datetime, timezone
from uuid import uuid4

from flask_restful import abort
from sqlalchemy import select, text

from config.db_config import db
from models.appointment_model import AppointmentModel
from models.completion_model import LocalSubscription
from models.consistency_model import PaymentIntent, ProviderTransaction
from models.payment_model import PaymentModel
from models.session_model import ProviderReceipt
from services.local_finance import apply_subscription, close_intent, local_only
from utils.booking_consistency import lock_appointment, snapshot_terms

BASE_PROPERTIES = {"transaction.id", "transaction.status", "transaction.amount_in_cents"}
FINANCIAL_PROPERTIES = BASE_PROPERTIES | {"transaction.currency", "transaction.reference"}
STATUSES = {"PENDING", "APPROVED", "DECLINED", "ERROR", "VOIDED"}


def create_intent(data):
    appointment = lock_appointment(data["appointment_id"])
    if data["status"] != "pending":
        return {"message": "Payment status is controlled by verified provider events"}, 403
    if appointment.status != "pending":
        return {"message": "Only pending bookings can start payment"}, 409
    terms = snapshot_terms(appointment)
    if data["amount"] != terms.amount or terms.amount <= 0:
        return {"message": "Amount must match the server booking price in COP"}, 400
    if data["paymentmethod"].lower() != "wompi":
        return {"message": "Only the verified Wompi workflow is supported"}, 400
    intent = PaymentIntent.query.filter_by(appointment_id=appointment.id).first()
    if intent is None and PaymentModel.query.filter_by(appointment_id=appointment.id).first():
        return {"message": "Legacy payment requires reconciliation before a new intent"}, 409
    created = intent is None
    if created:
        payment = PaymentModel(
            amount=terms.amount,
            paymentmethod="wompi",
            status="pending",
            appointment_id=appointment.id,
        )
        db.session.add(payment)
        db.session.flush()
        intent = PaymentIntent(
            reference=str(uuid4()),
            appointment_id=appointment.id,
            payment_id=payment.id,
            amount_in_cents=terms.amount * 100,
            currency="COP",
        )
        db.session.add(intent)
    else:
        payment = db.session.get(PaymentModel, intent.payment_id)
        if intent.state != "open" or intent.expires_at <= datetime.now(timezone.utc):
            return {"message": "Intent closed or expired; create a new booking"}, 409
    return {
        **payment.json(),
        "reference": intent.reference,
        "currency": intent.currency,
        "amount_in_cents": intent.amount_in_cents,
    }, 201 if created else 200


def process_event(body):
    transaction = body.get("data", {}).get("transaction", {})
    if not isinstance(transaction, dict):
        abort(400, message="Invalid transaction")
    identifier, status = transaction.get("id"), transaction.get("status")
    amount, currency, reference = (
        transaction.get("amount_in_cents"),
        transaction.get("currency"),
        transaction.get("reference"),
    )
    properties = set(body["signature"]["properties"])
    if not BASE_PROPERTIES.issubset(properties):
        abort(401, message="Provider signature must bind transaction identity, state and amount")
    if (
        body.get("environment") != "test"
        or body.get("event") != "transaction.updated"
        or not isinstance(identifier, str)
        or not 1 <= len(identifier) <= 150
        or not isinstance(status, str)
        or status not in STATUSES
        or type(amount) is not int
        or not 0 < amount <= 9_007_199_254_740_991
        or (reference is not None and (not isinstance(reference, str) or len(reference) > 150))
        or (currency is not None and (not isinstance(currency, str) or len(currency) != 3))
    ):
        abort(400, message="Only valid local test transactions accepted")
    if not FINANCIAL_PROPERTIES.issubset(properties):
        if reference is not None and (
            db.session.get(PaymentIntent, reference) is not None
            or db.session.get(LocalSubscription, reference) is not None
        ):
            abort(401, message="Financial reference and currency must be signed")
        # Preserve legacy receipt-only events. Unsigned metadata is stored only in the
        # raw receipt, never used as a financial lookup or immutable ledger identity.
        reference = currency = None
    # Lock even before a row exists. The composite PK is a second deduplication guard.
    db.session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": "wompi:" + identifier},
    )
    ledger = db.session.get(ProviderTransaction, ("wompi", identifier))
    if ledger:
        if (ledger.reference, ledger.currency, ledger.amount_in_cents) != (
            reference,
            currency,
            amount,
        ):
            abort(409, message="Provider transaction identity cannot change financial terms")
        if ledger.status == status or ledger.status == "APPROVED":
            return {
                "status": "received",
                "receipt_id": ledger.receipt_id,
                "duplicate": True,
                "payment_applied": ledger.applied_payment_id is not None,
                "reconciliation_required": ledger.resolution == "review",
            }, 202
        if ledger.status != "PENDING":
            abort(409, message="Terminal provider state cannot be changed")
    intent = db.session.get(PaymentIntent, reference) if reference else None
    subscription = (
        LocalSubscription.query.filter_by(reference=reference)
        .populate_existing()
        .with_for_update()
        .first()
        if reference and not intent
        else None
    )
    if subscription:
        local_only()
        if amount != subscription.amount_in_cents or currency != subscription.currency:
            abort(409, message="Subscription amount/currency mismatch")
    if intent:
        # Same row order as client booking/intent writes; never trust provider metadata as IDs.
        appointment = db.session.execute(
            select(AppointmentModel)
            .where(AppointmentModel.id == intent.appointment_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        ).scalar_one()
        db.session.refresh(intent)
        if amount != intent.amount_in_cents or currency != intent.currency:
            abort(409, message="Provider amount/currency does not match the server intent")
        if os.environ.get("LOCAL_RUNTIME") != "true" or os.environ.get("DATABASE_URL") != (
            "postgresql://synthetic:local-synthetic-only@postgres/fullstyle_synthetic"
        ):
            abort(503, message="Financial application is restricted to the synthetic local adapter")
    if ledger is None:
        receipt = ProviderReceipt(
            id=str(uuid4()),
            provider="wompi",
            transaction_id=identifier,
            payload=body,
            state="received",
        )
        db.session.add(receipt)
        db.session.flush()
        ledger = ProviderTransaction(
            provider="wompi",
            transaction_id=identifier,
            receipt_id=receipt.id,
            reference=reference,
            currency=currency,
            amount_in_cents=amount,
            status=status,
            verified_payload=body,
        )
        db.session.add(ledger)
    else:
        receipt = db.session.get(ProviderReceipt, ledger.receipt_id)
    if intent and status == "APPROVED":
        payment = db.session.get(PaymentModel, intent.payment_id)
        if intent.state == "open" and intent.expires_at <= datetime.now(timezone.utc):
            close_intent(intent, appointment, "expired")
        if intent.state in {"cancelled", "expired", "refunded"}:
            ledger.resolution = "review"
            receipt.state = "review"
        elif appointment.status != "pending" or payment.status != "pending":
            abort(
                409,
                message="Booking is no longer payable or already settled by another transaction",
            )
        else:
            payment.status = "paid"
            appointment.status = "paid"
            intent.state = "settled"
            ledger.applied_payment_id = payment.id
            ledger.resolution = "settled"
            receipt.state = "applied"
    if subscription and status == "APPROVED":
        apply_subscription(subscription, identifier)
        ledger.resolution = "settled"
        receipt.state = "applied"
    ledger.status = status
    ledger.verified_payload = body
    return {
        "status": "received",
        "receipt_id": receipt.id,
        "duplicate": False,
        "payment_applied": ledger.applied_payment_id is not None,
        "subscription_applied": bool(subscription and subscription.state == "active"),
        "reconciliation_required": ledger.resolution == "review",
    }, 202
