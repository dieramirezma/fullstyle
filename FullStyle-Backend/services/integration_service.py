"""Local provider boundaries: authorized quotas, mail delegation and event receipt."""

import hashlib
import hmac
import json
import os
import time
from uuid import uuid4

import jwt
import redis
from flask import Blueprint, g, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from config.db_config import db
from models.user_model import UserModel
from services.payment_workflow import process_event
from utils.authorization import authorized_appointment, principal_id
from utils.booking_consistency import transactional
from utils.mail_outbox import enqueue_mail

integrations = Blueprint("integrations", __name__)
quota = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), socket_timeout=2)


@integrations.errorhandler(HTTPException)
def integration_error(error):
    # Provider adapters must preserve controlled 4xx responses across Next's JSON boundary.
    message = getattr(error, "data", {}).get("message", error.description)
    return jsonify(message=message), error.code


def canonical(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def service_token(audience, payload):
    return jwt.encode(
        {
            "sub": "fullstyle-business",
            "type": "service",
            "aud": audience,
            "iat": int(time.time()),
            "exp": int(time.time()) + 60,
            "jti": uuid4().hex,
            "sha256": hashlib.sha256(canonical(payload).encode()).hexdigest(),
        },
        os.environ["INTEGRATION_SECRET"],
        algorithm="HS256",
    )


def consume_quota(user_id, action):
    if action not in {"upload", "geocode", "recaptcha", "contact", "payment", "email"}:
        return False
    # Atomic increment+expiry: no permanent key if a worker dies between commands.
    count = quota.eval(
        "local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],60) end; return n",
        1,
        f"provider-quota:{user_id}:{action}:{int(time.time()) // 60}",
    )
    return count <= 20


@integrations.post("/api/provider/authorize")
@jwt_required()
def authorize_provider():
    actor = principal_id()
    action = (request.get_json(silent=True) or {}).get("action")
    try:
        allowed = consume_quota(actor, action)
    except redis.RedisError:
        return jsonify(message="Quota unavailable"), 503
    if not allowed:
        return jsonify(message="Provider limit exceeded or unsupported action"), 429
    return jsonify(user=UserModel.find_by_id(actor).json(), mode="local")


@integrations.post("/api/email/<kind>")
@jwt_required()
def queue_email(kind):
    user = UserModel.find_by_id(principal_id())
    body = request.get_json(silent=True) or {}
    try:
        if not consume_quota(user.id, "email"):
            return jsonify(message="Email limit exceeded"), 429
    except redis.RedisError:
        return jsonify(message="Quota unavailable"), 503
    # Recipient is always derived from the active SQL identity, never the request.
    if kind == "contact":
        text = body.get("message", "")
        if not isinstance(text, str) or not 1 <= len(text) <= 2000:
            return jsonify(message="Message must contain 1-2000 characters"), 400
        payload = {"email": user.email, "name": user.name, "message": text}
    else:
        # Transactional mail requires an actual authorized booking. Delivery templates
        # requiring payment confirmation remain disabled until the payment ledger exists.
        if not isinstance(body.get("appointmentId"), int):
            return jsonify(message="appointmentId required"), 400
        authorized_appointment(body["appointmentId"])
        return jsonify(message="Transactional mail requires verified payment workflow"), 503
    try:
        event_id = enqueue_mail(
            "contact",
            payload,
            operation_id=f"contact:{user.id}:{g.operation_id}",
            correlation_id=g.correlation_id,
        )
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify(message="Mail storage unavailable"), 503
    return jsonify(message="Email task queued successfully", event_id=event_id), 202


def valid_checksum(body, checksum):
    try:
        properties = body["signature"]["properties"]
        if not isinstance(properties, list) or not 1 <= len(properties) <= 30:
            return False
        values = []
        for path in properties:
            value = body["data"]
            if not isinstance(path, str) or len(path) > 200:
                return False
            for part in path.split("."):
                if part in {"__proto__", "constructor", "prototype"}:
                    return False
                value = value[part]
            if type(value) not in (str, int, float, bool):
                return False
            values.append(str(value).lower() if isinstance(value, bool) else str(value))
        if type(body["timestamp"]) is not int:
            return False
        calculated = hashlib.sha256(
            ("".join(values) + str(body["timestamp"]) + os.environ["WOMPI_EVENTS_KEY"]).encode()
        ).hexdigest()
        return isinstance(checksum, str) and hmac.compare_digest(calculated, checksum.lower())
    except (KeyError, TypeError, ValueError):
        return False


@integrations.post("/api/integrations/wompi/events")
@transactional
def receive_event():
    body = request.get_json(silent=True)
    try:
        claims = jwt.decode(
            request.headers.get("Authorization", "").removeprefix("Bearer "),
            os.environ["INTEGRATION_SECRET"],
            algorithms=["HS256"],
            audience="wompi.receipt",
            options={"require": ["sub", "type", "exp", "iat", "jti", "sha256"]},
        )
        digest = hashlib.sha256(request.get_data()).hexdigest()
        if (
            claims["type"] != "service"
            or claims["sub"] != "fullstyle-next"
            or not hmac.compare_digest(claims["sha256"], digest)
        ):
            raise ValueError("Invalid delegation")
    except (jwt.PyJWTError, ValueError):
        return jsonify(message="Restricted service identity required"), 401
    if not isinstance(body, dict) or not valid_checksum(
        body, request.headers.get("X-Event-Checksum")
    ):
        return jsonify(message="Invalid provider checksum"), 401
    payload, status = process_event(body)
    return payload, status
