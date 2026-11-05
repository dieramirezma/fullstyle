"""Persist a mail intent before acknowledging it; RabbitMQ is dispatched separately."""

import hashlib
import json
from uuid import uuid4

from flask_restful import abort
from sqlalchemy.dialects.postgresql import insert

from config.db_config import db
from models.reliability_model import MailEvent


def enqueue_mail(kind, data, operation_id=None, correlation_id=None):
    event_id = hashlib.sha256((operation_id or uuid4().hex).encode()).hexdigest()
    content = {"email_type": kind, "data": data}
    digest = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
    payload = {
        **content,
        "event_type": "mail.requested",
        "event_version": 1,
        "event_id": event_id,
        "correlation_id": correlation_id or uuid4().hex,
    }
    db.session.execute(
        insert(MailEvent)
        .values(id=event_id, payload=payload, payload_hash=digest)
        .on_conflict_do_nothing()
    )
    event = db.session.get(MailEvent, event_id)
    if event.payload_hash != digest:
        db.session.rollback()
        abort(409, message="Operation already used for a different mail intent")
    db.session.commit()
    return event_id
