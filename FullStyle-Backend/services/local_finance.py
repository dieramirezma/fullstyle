"""Synthetic-only lifecycle. No provider calls, arbitrary prices or audit deletion."""

import os
import re
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from flask_restful import abort

from config.db_config import db
from models.completion_model import LocalSubscription, PaymentAction
from models.consistency_model import PaymentIntent, ProviderTransaction
from models.manager_model import ManagerModel
from models.payment_model import PaymentModel
from utils.authorization import principal_id, require_manager, require_site
from utils.booking_consistency import lock_appointment, lock_workers

PLAN = {
    "id": "synthetic-30-days",
    "name": "Prueba local de 30 días",
    "amount_in_cents": 1_000_000,
    "currency": "COP",
    "days": 30,
    "synthetic": True,
}


def local_only():
    if (
        os.getenv("LOCAL_RUNTIME") != "true"
        or os.getenv("DATABASE_URL")
        != "postgresql://synthetic:local-synthetic-only@postgres/fullstyle_synthetic"
    ):
        abort(503, message="Synthetic local workflow only")


def close_intent(intent, appointment, reason):
    if intent.state == "open":
        lock_workers(appointment.worker_id)
        payment = db.session.get(PaymentModel, intent.payment_id)
        if payment.status != "pending" or appointment.status != "pending":
            abort(409, message="Settled booking requires a refund")
        intent.state = reason
        payment.status = reason
        appointment.status = "cancelled"


def intent_view(intent):
    return {
        "reference": intent.reference,
        "appointment_id": intent.appointment_id,
        "state": intent.state,
        "expires_at": intent.expires_at.isoformat(),
        "amount_in_cents": intent.amount_in_cents,
        "currency": intent.currency,
        "synthetic": True,
    }


def manage_intent(reference, action=None):
    local_only()
    intent = db.session.get(PaymentIntent, reference)
    if not intent:
        abort(404, message="Intent not found")
    appointment = lock_appointment(intent.appointment_id)
    db.session.refresh(intent)
    if intent.expires_at <= datetime.now(timezone.utc):
        close_intent(intent, appointment, "expired")
    if action == "cancel":
        if intent.state not in {"open", "cancelled", "expired"}:
            abort(409, message="Settled booking requires a refund")
        close_intent(intent, appointment, "cancelled")
    return intent_view(intent)


def reconcile(site_id):
    local_only()
    require_site(site_id)
    from models.appointment_model import AppointmentModel

    rows = (
        db.session.query(ProviderTransaction, PaymentIntent)
        .join(PaymentIntent, ProviderTransaction.reference == PaymentIntent.reference)
        .join(AppointmentModel, AppointmentModel.id == PaymentIntent.appointment_id)
        .filter(AppointmentModel.site_id == site_id)
        .order_by(ProviderTransaction.transaction_id)
        .all()
    )
    return [
        {
            "transaction_id": row.transaction_id,
            "reference": row.reference,
            "status": row.status,
            "resolution": row.resolution,
            "payment_id": intent.payment_id,
            "appointment_id": intent.appointment_id,
            "amount_in_cents": row.amount_in_cents,
            "currency": row.currency,
        }
        for row, intent in rows
    ]


def refund(transaction_id, body):
    local_only()
    if (
        not isinstance(body, dict)
        or not isinstance(body.get("reason"), str)
        or not 1 <= len(body["reason"].strip()) <= 500
        or not re.fullmatch(r"[A-Za-z0-9._:-]{1,80}", str(body.get("operation_id", "")))
    ):
        abort(400, message="Reason and operation_id required")
    # Same order as events: transaction lock, appointment, worker.
    from sqlalchemy import text

    db.session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key,0))"),
        {"key": "wompi:" + transaction_id},
    )
    row = db.session.get(ProviderTransaction, ("wompi", transaction_id))
    intent = db.session.get(PaymentIntent, row.reference) if row else None
    if not intent or row.status != "APPROVED":
        abort(409, message="Verified approved booking charge required")
    appointment = lock_appointment(intent.appointment_id)
    require_site(appointment.site_id)
    prior = db.session.get(PaymentAction, body["operation_id"])
    if prior and (prior.payment_id, prior.actor_id, prior.transaction_id, prior.reason) != (
        intent.payment_id,
        principal_id(),
        transaction_id,
        body["reason"],
    ):
        abort(409, message="Operation identity reused")
    if row.resolution == "refunded":
        return {"synthetic": True, "state": "refunded", "duplicate": True}
    if prior:
        abort(409, message="Operation already used")
    lock_workers(appointment.worker_id)
    if row.applied_payment_id:
        db.session.get(PaymentModel, intent.payment_id).status = "refunded"
        appointment.status = "cancelled"
        intent.state = "refunded"
    row.resolution = "refunded"
    db.session.add(
        PaymentAction(
            operation_id=body["operation_id"],
            payment_id=intent.payment_id,
            actor_id=principal_id(),
            transaction_id=transaction_id,
            action="synthetic_refund",
            reason=body["reason"],
        )
    )
    return {"synthetic": True, "state": "refunded", "duplicate": False}


def subscription_view(row):
    now = datetime.now(timezone.utc)
    return {
        "reference": row.reference,
        "plan": row.plan,
        "amount_in_cents": row.amount_in_cents,
        "currency": row.currency,
        "state": "expired" if row.expires_at and row.expires_at <= now else row.state,
        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
        "synthetic": True,
    }


def create_subscription(body):
    local_only()
    require_manager()
    if not isinstance(body, dict) or set(body) - {"plan"} or body.get("plan") != PLAN["id"]:
        abort(400, message="Choose a server catalog plan; price and status cannot be supplied")
    # Serialize requests across tabs. A pending intent is reused, never extended by retries.
    ManagerModel.query.filter_by(id=principal_id()).with_for_update().one()
    row = LocalSubscription.query.filter_by(user_id=principal_id(), state="pending").first()
    if not row:
        row = LocalSubscription(
            reference=str(uuid4()),
            user_id=principal_id(),
            plan=PLAN["id"],
            amount_in_cents=PLAN["amount_in_cents"],
            currency=PLAN["currency"],
        )
        db.session.add(row)
        db.session.flush()
    return subscription_view(row)


def apply_subscription(row, transaction_id):
    local_only()
    manager = (
        ManagerModel.query.filter_by(id=row.user_id).populate_existing().with_for_update().one()
    )
    if row.state != "pending":
        abort(409, message="Subscription already settled")
    now = datetime.now(timezone.utc)
    start = max(now, manager.subscriptionfinishdate or now)
    row.state = "active"
    row.expires_at = start + timedelta(days=PLAN["days"])
    row.provider_transaction_id = transaction_id
    manager.subscriptionactive = True
    manager.subscriptiontype = PLAN["id"]
    manager.subscriptionstartdate = now
    manager.subscriptionfinishdate = row.expires_at
