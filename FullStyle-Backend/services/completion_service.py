"""Authenticated local workflows and password-plus-offline-code MFA recovery."""

import hashlib
import re
import time
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required
from flask_restful import abort
from sqlalchemy import func
from werkzeug.exceptions import HTTPException

from config.db_config import db
from models.completion_model import LocalSubscription, MailReview
from models.consistency_model import BookingTerms, PaymentIntent
from models.reliability_model import MailDelivery, MailEvent
from models.user_model import UserModel
from services.local_finance import (
    PLAN,
    create_subscription,
    local_only,
    manage_intent,
    reconcile,
    refund,
    subscription_view,
)
from utils.account_security import policy, session_valid, verify_otp
from utils.authorization import authorized_appointment, principal_id, require_manager
from utils.booking_consistency import transactional
from utils.mfa_recovery import consume_code, issue_codes

completion = Blueprint("completion", __name__)


@completion.errorhandler(HTTPException)
def controlled_error(error):
    return jsonify(message=getattr(error, "data", {}).get("message", error.description)), error.code


@completion.route("/api/payment/intents/<reference>", methods=["GET", "DELETE"])
@jwt_required()
@transactional
def payment_intent(reference):
    return manage_intent(reference, "cancel" if request.method == "DELETE" else None)


@completion.get("/api/payment/reconciliation")
@jwt_required()
def payment_reconciliation():
    site_id = request.args.get("site_id", type=int)
    if not site_id:
        return {"message": "site_id required"}, 400
    return jsonify(transactions=reconcile(site_id))


@completion.get("/api/payment/quote/<int:appointment_id>")
@jwt_required()
def payment_quote(appointment_id):
    local_only()
    appointment = authorized_appointment(appointment_id)
    terms = db.session.get(BookingTerms, appointment_id)
    if appointment.status != "pending" or not terms or terms.amount <= 0:
        return {"message": "Pending priced booking required"}, 409
    return {
        "appointment_id": appointment_id,
        "amount": terms.amount,
        "currency": terms.currency,
        "synthetic": True,
    }


@completion.post("/api/payment/refunds/<transaction_id>")
@jwt_required()
@transactional
def payment_refund(transaction_id):
    return refund(transaction_id, request.get_json(silent=True))


@completion.get("/api/subscriptions/catalog")
@jwt_required()
def subscription_catalog():
    local_only()
    return jsonify(plans=[PLAN])


@completion.route("/api/subscriptions", methods=["GET", "POST"])
@jwt_required()
@transactional
def subscriptions():
    local_only()
    require_manager()
    if request.method == "POST":
        return create_subscription(request.get_json(silent=True)), 201
    return jsonify(
        subscriptions=[
            subscription_view(row)
            for row in LocalSubscription.query.filter_by(user_id=principal_id()).all()
        ]
    )


@completion.post("/api/local/payments/simulate")
@jwt_required()
@transactional
def simulate_payment():
    local_only()
    body = request.get_json(silent=True)
    if (
        not isinstance(body, dict)
        or not isinstance(body.get("reference"), str)
        or not re.fullmatch(r"[A-Za-z0-9._:-]{1,80}", str(body.get("operation_id", "")))
    ):
        return {"message": "Reference and operation_id required"}, 400
    reference = body["reference"]
    intent = db.session.get(PaymentIntent, reference)
    subscription = db.session.get(LocalSubscription, reference)
    if intent:
        authorized_appointment(intent.appointment_id)
        amount, currency = intent.amount_in_cents, intent.currency
    elif subscription and subscription.user_id == principal_id():
        amount, currency = subscription.amount_in_cents, subscription.currency
    else:
        abort(404, message="Reference not found")
    from services.payment_workflow import FINANCIAL_PROPERTIES, process_event

    event = {
        "event": "transaction.updated",
        "environment": "test",
        "timestamp": int(time.time()),
        "data": {
            "transaction": {
                "id": "synthetic-"
                + hashlib.sha256((reference + ":" + body["operation_id"]).encode()).hexdigest(),
                "status": "APPROVED",
                "amount_in_cents": amount,
                "currency": currency,
                "reference": reference,
            }
        },
        "signature": {"properties": sorted(FINANCIAL_PROPERTIES)},
    }
    result, status = process_event(event)
    return {
        **result,
        "synthetic": True,
        "transaction_id": event["data"]["transaction"]["id"],
    }, status


@completion.get("/api/mail/events")
@jwt_required()
def mail_events():
    local_only()
    user = db.session.get(UserModel, principal_id())
    rows = (
        MailEvent.query.filter(MailEvent.payload["data"]["email"].as_string() == user.email)
        .order_by(MailEvent.created_at.desc())
        .limit(100)
        .all()
    )
    return jsonify(
        events=[
            {
                "event_id": row.id,
                "state": row.state,
                "attempts": row.attempts,
                "last_error": row.last_error,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    )


@completion.post("/api/mail/events/<event_id>/retry")
@jwt_required()
@transactional
def retry_mail(event_id):
    local_only()
    user = db.session.get(UserModel, principal_id())
    row = (
        MailEvent.query.filter(
            MailEvent.id == event_id, MailEvent.payload["data"]["email"].as_string() == user.email
        )
        .populate_existing()
        .with_for_update()
        .first()
    )
    if not row:
        return {"message": "Event not found"}, 404
    body = request.get_json(silent=True)
    if (
        not isinstance(body, dict)
        or not isinstance(body.get("reason"), str)
        or not 1 <= len(body["reason"].strip()) <= 500
        or not re.fullmatch(r"[A-Za-z0-9._:-]{1,80}", str(body.get("operation_id", "")))
    ):
        return {"message": "Reason and operation_id required"}, 400
    prior = db.session.get(MailReview, body["operation_id"])
    if prior:
        if (prior.event_id, prior.actor_id, prior.reason) != (event_id, user.id, body["reason"]):
            return {"message": "Operation identity reused"}, 409
        return {"event_id": event_id, "duplicate": True, "state": row.state}, 200
    if row.state == "delivered" or MailDelivery.query.filter_by(event_id=event_id).first():
        return {"message": "Delivered mail cannot be replayed"}, 409
    # A poisoned payload must be fixed by its producer; review cannot mutate it.
    if row.payload.get("email_type") != "contact" or set(row.payload.get("data", {})) != {
        "email",
        "name",
        "message",
    }:
        return {"message": "Only validated local contact messages can be requeued"}, 409
    row.state = "pending"
    row.next_attempt = datetime.now(timezone.utc)
    row.last_error = None
    db.session.add(
        MailReview(
            operation_id=body["operation_id"],
            event_id=event_id,
            actor_id=user.id,
            reason=body["reason"],
        )
    )
    return {"event_id": event_id, "duplicate": False, "state": "pending"}, 200


@completion.post("/api/mfa/recover")
@transactional
def recover_mfa():
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not all(
        isinstance(body.get(k), str) and 0 < len(body[k]) <= 320
        for k in ("email", "password", "recovery_code")
    ):
        return {"message": "Email, password and recovery code required"}, 400
    user = UserModel.query.filter_by(email=body["email"], active=True).first()
    if user is None:
        candidates = (
            UserModel.query.filter(
                func.lower(UserModel.email) == body["email"].lower(), UserModel.active.is_(True)
            )
            .limit(2)
            .all()
        )
        user = candidates[0] if len(candidates) == 1 else None
    if not user:
        return {"message": "Recovery rejected"}, 401
    state = policy(user.id, lock=True)
    db.session.refresh(user)
    if not user.active or not user.check_password(body["password"]) or not state.enabled:
        return {"message": "Recovery rejected"}, 401
    if not consume_code(state, body["recovery_code"]):
        # Persist lockout even though the request is rejected.
        db.session.commit()
        return {"message": "Recovery rejected"}, 401
    return {
        "message": "Authenticator removed and all sessions revoked. Sign in and enroll again."
    }, 200


@completion.post("/api/mfa/recovery-codes")
@jwt_required()
@transactional
def regenerate_recovery_codes():
    user = db.session.get(UserModel, principal_id())
    body = request.get_json(silent=True) or {}
    state = policy(user.id, lock=True)
    db.session.refresh(user)
    if (
        not isinstance(body, dict)
        or not user.check_password(body.get("password", ""))
        or not session_valid(get_jwt(), user.id)
    ):
        return {"message": "Current password required"}, 401
    if not state.enabled or not verify_otp(state, body.get("otp", "")):
        db.session.commit()
        return {"message": "Fresh OTP required"}, 401
    return jsonify(recovery_codes=issue_codes(user.id))
