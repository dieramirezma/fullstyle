"""Shared SQL history, per-conversation exclusion and durable operation receipts."""

import hashlib
import os
import re

import psycopg2
from psycopg2.extras import RealDictCursor

EXPECTED = "postgresql://synthetic:local-synthetic-only@postgres/fullstyle_synthetic"


class StoreError(Exception):
    def __init__(self, status_code, detail):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def connect():
    if os.getenv("LOCAL_RUNTIME") != "true" or os.getenv("DATABASE_URL") != EXPECTED:
        raise StoreError(status_code=503, detail="Shared history unavailable")
    schema = os.getenv("RELIABILITY_SCHEMA", "public")
    if schema != "public" and not re.fullmatch(
        r"(?:phase5_[a-f0-9]{12}|phase6_[a-f0-9]{32})", schema
    ):
        raise ValueError("Unexpected schema")
    return psycopg2.connect(
        EXPECTED,
        connect_timeout=3,
        options=f"-c search_path={schema} -c statement_timeout=5000 -c lock_timeout=2000",
        cursor_factory=RealDictCursor,
    )


class Conversation:
    def __init__(self, user_id, session_id, operation_id, message):
        self.key = (user_id, session_id)
        self.operation_id = operation_id
        self.message = message
        self.conn = None
        self.sequence = None
        self.replayed = False

    def begin(self):
        self.conn = connect()
        with self.conn, self.conn.cursor() as cur:
            cur.execute(
                "SELECT pg_try_advisory_lock(hashtextextended(%s,0)) AS acquired",
                (f"chat:{self.key[0]}:{self.key[1]}",),
            )
            if not cur.fetchone()["acquired"]:
                raise StoreError(status_code=409, detail="Conversation has an active request")
            cur.execute(
                "SELECT * FROM chat_turn WHERE user_id=%s AND session_id=%s AND operation_id=%s",
                (*self.key, self.operation_id),
            )
            previous = cur.fetchone()
            if previous:
                if previous["message_hash"] != hashlib.sha256(self.message.encode()).hexdigest():
                    raise StoreError(
                        status_code=409, detail="Operation reused with a different message"
                    )
                if previous["state"] != "completed":
                    raise StoreError(
                        status_code=409,
                        detail="Previous operation has an uncertain outcome; review before a new action",
                    )
                self.replayed = True
                return previous["reply"], []
            # Pending rows left by a crashed replica remain visible as uncertain outcomes.
            cur.execute(
                "UPDATE chat_turn SET state='uncertain' WHERE user_id=%s AND session_id=%s AND state='pending'",
                self.key,
            )
            cur.execute(
                "SELECT message,reply FROM chat_turn WHERE user_id=%s AND session_id=%s AND state='completed' ORDER BY sequence DESC LIMIT 5",
                self.key,
            )
            history = [
                (role, row[field])
                for row in reversed(cur.fetchall())
                for role, field in (("human", "message"), ("ai", "reply"))
            ]
            cur.execute(
                "INSERT INTO chat_turn(user_id,session_id,operation_id,message,message_hash) VALUES(%s,%s,%s,%s,%s) RETURNING sequence",
                (
                    *self.key,
                    self.operation_id,
                    self.message,
                    hashlib.sha256(self.message.encode()).hexdigest(),
                ),
            )
            self.sequence = cur.fetchone()["sequence"]
        return None, history

    def complete(self, reply):
        with self.conn, self.conn.cursor() as cur:
            cur.execute(
                "UPDATE chat_turn SET state='completed',reply=%s WHERE sequence=%s AND state='pending'",
                (reply, self.sequence),
            )
            if cur.rowcount != 1:
                raise RuntimeError("Chat operation lost its pending receipt")

    def close(self):
        if self.conn is not None:
            self.conn.close()  # Also releases the session advisory lock after crashes/errors.


def history(user_id, session_id):
    conn = connect()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "SELECT sequence,message,reply,state,operation_id,reviewed_at,review_note FROM chat_turn WHERE user_id=%s AND session_id=%s ORDER BY sequence DESC LIMIT 50",
                (user_id, session_id),
            )
            return list(reversed(cur.fetchall()))
    finally:
        conn.close()


def review(user_id, session_id, operation_id, note):
    conn = connect()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "SELECT pg_try_advisory_xact_lock(hashtextextended(%s,0)) AS acquired",
                (f"chat:{user_id}:{session_id}",),
            )
            if not cur.fetchone()["acquired"]:
                raise StoreError(status_code=409, detail="Operation is still running")
            cur.execute(
                "SELECT state FROM chat_turn WHERE user_id=%s AND session_id=%s AND operation_id=%s FOR UPDATE",
                (user_id, session_id, operation_id),
            )
            row = cur.fetchone()
            if not row:
                raise StoreError(status_code=404, detail="Operation not found")
            if row["state"] == "completed":
                raise StoreError(status_code=409, detail="Completed operation needs no review")
            if row["state"] != "reviewed":
                cur.execute(
                    "UPDATE chat_turn SET state='reviewed', reviewed_at=now(),review_note=%s WHERE user_id=%s AND session_id=%s AND operation_id=%s",
                    (note, user_id, session_id, operation_id),
                )
        return {"state": "reviewed", "operation_id": operation_id, "reexecuted": False}
    finally:
        conn.close()


def redact_expired():
    """Keep operation tombstones for dedup; never erase unresolved evidence."""
    conn = connect()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE chat_turn SET message='',reply='Contenido expirado por retención',review_note=NULL WHERE sequence IN (SELECT sequence FROM chat_turn WHERE content_expires_at < now() AND state IN ('completed','reviewed') AND message != '' ORDER BY sequence LIMIT 500 FOR UPDATE SKIP LOCKED)"
            )
            return cur.rowcount
    finally:
        conn.close()
