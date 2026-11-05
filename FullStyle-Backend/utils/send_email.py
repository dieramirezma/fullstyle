"""Durable local reset mail; provider delivery remains disabled."""

import json
import os

import redis
from flask import g

from utils.mail_outbox import enqueue_mail


def ResetPassword(email, name, token):
    if os.getenv("LOCAL_RUNTIME") != "true":
        raise RuntimeError("External password-reset delivery disabled")
    reset_link = f"{os.environ['APP_WEB_URL']}password_reset?token={token}"
    event_id = enqueue_mail(
        "reset_password",
        {"email": email, "name": name, "reset_link": reset_link},
        correlation_id=g.correlation_id,
    )
    try:
        client = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            db=2,
            socket_timeout=0.3,
            socket_connect_timeout=0.3,
        )
        client.lpush("local-reset-outbox", json.dumps({"email": email, "reset_link": reset_link}))
        client.ltrim("local-reset-outbox", 0, 99)
    except redis.RedisError:
        pass  # Compatibility projection only; the SQL intent was committed.
    return {"mode": "local", "event_id": event_id}
