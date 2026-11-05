"""PostgreSQL outbox and transactional LOCAL receipts; never external exactly-once."""

import hashlib
import json
import os
from contextvars import ContextVar

import psycopg2
from psycopg2.extras import Json, RealDictCursor

delivery_context = ContextVar("mail_delivery", default=None)
EXPECTED = "postgresql://synthetic:local-synthetic-only@postgres/fullstyle_synthetic"


def connect():
    if os.getenv("LOCAL_RUNTIME") != "true" or os.getenv("DATABASE_URL") != EXPECTED:
        raise RuntimeError("Durable mail is restricted to the synthetic database")
    schema = os.getenv("RELIABILITY_SCHEMA", "public")
    if schema != "public" and not (schema.startswith("phase5_") and schema.isidentifier()):
        raise ValueError("Unexpected schema")
    return psycopg2.connect(
        EXPECTED,
        connect_timeout=3,
        options=f"-c search_path={schema} -c statement_timeout=5000 -c lock_timeout=2000",
        cursor_factory=RealDictCursor,
    )


def normalize(message, message_id=None):
    if not isinstance(message, dict):
        raise ValueError("JSON object required")
    version = message.get("event_version", 0)
    if type(version) is not int or version not in (0, 1):
        raise ValueError("Unsupported mail event version")
    if version == 1 and message.get("event_type") != "mail.requested":
        raise ValueError("Unsupported event type")
    if not isinstance(message.get("data"), dict) or not isinstance(message.get("email_type"), str):
        raise ValueError("Invalid mail payload")
    content = {"email_type": message["email_type"], "data": message["data"]}
    digest = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
    event_id = message.get("event_id") or message_id or "legacy-" + digest[:57]
    if not isinstance(event_id, str) or not 1 <= len(event_id) <= 64:
        raise ValueError("Invalid event ID")
    return event_id, digest


def persist(message, message_id=None):
    event_id, digest = normalize(message, message_id)
    conn = connect()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO mail_event(id,payload,payload_hash) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING",
                (event_id, Json(message), digest),
            )
            cur.execute("SELECT payload_hash FROM mail_event WHERE id=%s", (event_id,))
            if cur.fetchone()["payload_hash"] != digest:
                raise ValueError("Event ID reused with different content")
    finally:
        conn.close()
    return event_id


def record_delivery(result):
    context = delivery_context.get()
    if context is None:
        raise RuntimeError("Delivery requires an active durable event")
    conn, event_id, ordinal = context
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO mail_delivery(event_id,ordinal,result) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING",
            (event_id, ordinal, Json(result)),
        )
    delivery_context.set((conn, event_id, ordinal + 1))
    return result


def dispatch_one(rabbitmq, queue="email_queue"):
    """A stable event ID makes retry after an uncertain broker confirm safe."""
    conn = connect()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM mail_event WHERE state='pending' AND next_attempt<=now() ORDER BY next_attempt,id FOR UPDATE SKIP LOCKED LIMIT 1"
            )
            event = cur.fetchone()
            if not event:
                return False
            error = None
            try:
                rabbitmq.publish_message(queue, event["payload"])
            except Exception as exc:
                error = type(exc).__name__
            delay = min(30, 2 ** min(event["attempts"] + 1, 5)) if error else 30
            cur.execute(
                "UPDATE mail_event SET attempts=attempts+1,last_error=%s,next_attempt=now()+(%s * interval '1 second') WHERE id=%s",
                (error, delay, event["id"]),
            )
        return True
    finally:
        conn.close()
