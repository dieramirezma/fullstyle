"""Compatible routes acknowledge durable SQL acceptance, not SMTP delivery."""

import hashlib
import os

import psycopg2
from flask import Blueprint, g, jsonify, request

from services.durable_mail import persist

email_bp = Blueprint("email", __name__, url_prefix="/api/emails")
KINDS = {
    "subscription": "subscription",
    "reset-password": "reset_password",
    "contact": "contact",
    "appointment/confirmation": "appointment_confirmation",
    "appointment/partial-payment": "partial_payment_confirmation",
    "appointment/rejected": "appointment_rejected",
    "appointment/canceled": "appointment_canceled",
}


@email_bp.post("/<path:kind>")
def enqueue(kind):
    if kind not in KINDS:
        return jsonify(error="Unknown mail route"), 404
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not payload:
        return jsonify(error="JSON object required"), 400
    event_id = hashlib.sha256((g.mail_operation + ":" + kind).encode()).hexdigest()
    message = {"email_type": KINDS[kind], "data": payload, "event_id": event_id}
    if os.getenv("MAIL_EVENT_VERSION", "0") == "1":
        message.update(event_type="mail.requested", event_version=1)
    try:
        persist(message)
    except ValueError:
        return jsonify(error="Operation already used for different mail content"), 409
    except psycopg2.Error:
        return jsonify(error="Mail storage unavailable"), 503
    return jsonify(message="Email task queued successfully", event_id=event_id), 200
