"""Disposable Redis responses keyed by a PostgreSQL generation committed with data."""

import hashlib
import json
import os
from functools import wraps
from uuid import uuid4

import redis
from flask import current_app, request
from sqlalchemy import event, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from config.db_config import db
from models.consistency_model import CacheEpoch

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True,
    socket_timeout=0.3,
    socket_connect_timeout=0.3,
)


@event.listens_for(Session, "before_flush")
def update_cache_epochs(session, flush_context, instances):
    # Executed in the SAME SQL transaction as ORM writes, including legacy services.
    # Redis invalidation is never necessary for correctness, even during an outage.
    namespaces = set()
    booking_tables = {
        "appointment",
        "booking_terms",
        "worker",
        "site",
        "manager",
        "detail",
        "service",
        "availability",
        "days_off",
        "seasonal_schedule",
    }
    for item in session.new | session.dirty | session.deleted:
        table = getattr(item, "__tablename__", "")
        if table in booking_tables:
            namespaces.add("appointments")
        if table == "category":
            namespaces.add("categories")
    for namespace in sorted(namespaces):
        statement = insert(CacheEpoch).values(namespace=namespace, generation=uuid4().hex)
        session.execute(
            statement.on_conflict_do_update(
                index_elements=[CacheEpoch.namespace],
                set_={"generation": statement.excluded.generation},
            )
        )


def generate_cache_key(func_name, args, kwargs, query_params=None):
    # Resource instances are request-local and must never enter the key.
    encoded = json.dumps([func_name, kwargs, query_params], sort_keys=True, default=str)
    return "cache:v4:" + hashlib.sha256(encoded.encode()).hexdigest()


def cache_result(ttl=300, use_request_args=True, namespace="categories", private=False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from utils.authorization import principal_id

            actor = principal_id() if private else None
            generation = (
                db.session.execute(
                    select(CacheEpoch.generation).where(CacheEpoch.namespace == namespace)
                ).scalar_one_or_none()
                or "empty"
            )
            query = sorted(request.args.items(multi=True)) if use_request_args else None
            identity = [
                namespace,
                generation,
                actor,
                current_app.config["SQLALCHEMY_DATABASE_URI"],
                db.session.execute(select(db.func.current_schema())).scalar_one(),
            ]
            key = generate_cache_key(
                func.__module__ + "." + func.__qualname__,
                (),
                {"scope": identity, "kwargs": kwargs},
                query,
            )
            try:
                cached = redis_client.get(key)
                if cached:
                    envelope = json.loads(cached)
                    if (
                        envelope.get("version") == 4
                        and type(envelope.get("status")) is int
                        and envelope["status"] in (200, 404)
                    ):
                        return envelope["body"], envelope["status"]
            except (redis.RedisError, ValueError, TypeError, KeyError, AttributeError):
                pass
            # Business logic is called ONCE. Cache failures cannot retry an operation.
            result = func(*args, **kwargs)
            if isinstance(result, tuple) and len(result) == 2 and result[1] in (200, 404):
                try:
                    encoded = json.dumps({"version": 4, "body": result[0], "status": result[1]})
                    redis_client.setex(key, ttl, encoded)
                except (redis.RedisError, ValueError, TypeError):
                    pass
            return result

        return wrapper

    return decorator


def invalidate_cache_pattern(pattern):
    """Optional memory cleanup. SQL epochs provide transactional invalidation."""
    # v4 keys are opaque and expire; never scan/flush unrelated keys or quota data.
    return None


def get_cache_stats():
    try:
        info = redis_client.info("memory")
        return {"status": "healthy", "used_memory": info["used_memory_human"]}
    except redis.RedisError:
        return {"status": "unavailable"}


CACHE_TTL = {
    "categories": 3600,
    "sites": 1800,
    "workers": 900,
    "appointments": 300,
    "statistics": 1800,
    "availability": 600,
    "services": 1800,
}
