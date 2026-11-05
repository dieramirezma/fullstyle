"""Recoverable mail: durable dispatch, explicit ack, SQL dedup and quarantine."""

import json
import logging
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_email_app
from config.rabbitmq_config import rabbitmq
from services.durable_mail import connect, delivery_context, dispatch_one, normalize, persist
from services.email_service import EmailService

logger = logging.getLogger(__name__)
METHODS = {
    "subscription": "send_subscription_confirmation",
    "reset_password": "send_reset_password",
    "contact": "send_contact_email",
    "appointment_confirmation": "send_appointment_confirmation",
    "partial_payment_confirmation": "send_partial_payment_confirmation",
    "appointment_rejected": "send_appointment_rejected",
    "appointment_canceled": "send_appointment_canceled",
}


class EmailWorker:
    def __init__(self):
        self.app = create_email_app()
        self.email_service = EmailService()

    def deliver(self, message, message_id=None):
        event_id, _ = normalize(message, message_id)
        persist(message, message_id)
        conn = connect()
        try:
            with conn, conn.cursor() as cur:
                cur.execute("SELECT * FROM mail_event WHERE id=%s FOR UPDATE", (event_id,))
                event = cur.fetchone()
                if event["state"] in ("delivered", "dead"):
                    return "duplicate"
                token = delivery_context.set((conn, event_id, 0))
                try:
                    method = METHODS.get(message["email_type"])
                    if method is None:
                        raise ValueError("Unknown email type")
                    with self.app.app_context():
                        getattr(self.email_service, method)(**message["data"])
                    cur.execute(
                        "UPDATE mail_event SET state='delivered',delivered_at=now(),last_error=NULL WHERE id=%s",
                        (event_id,),
                    )
                finally:
                    delivery_context.reset(token)
            self.project_local(event_id)
            return "delivered"
        finally:
            conn.close()

    def project_local(self, event_id):
        # Optional legacy view; SQL is the authoritative synthetic effect.
        import redis

        try:
            conn = connect()
            try:
                with conn, conn.cursor() as cur:
                    cur.execute(
                        "SELECT result FROM mail_delivery WHERE event_id=%s ORDER BY ordinal",
                        (event_id,),
                    )
                    results = [row["result"] for row in cur.fetchall()]
            finally:
                conn.close()
            client = redis.Redis(
                host=os.getenv("REDIS_HOST", "redis"),
                db=2,
                socket_connect_timeout=0.3,
                socket_timeout=0.3,
            )
            for result in results:
                client.lpush("local-mail-outbox", json.dumps(result))
                client.ltrim("local-mail-outbox", 0, 99)
        except Exception:
            logger.warning("Optional Redis mail projection unavailable")

    def process_email_task(self, ch, method, properties, body):
        started = time.monotonic()
        outcome = "retry"
        try:
            if len(body) > 65536:
                raise ValueError("Oversized mail event")
            message = json.loads(body)
            outcome = self.deliver(message, properties.message_id)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except (ValueError, TypeError, KeyError) as exc:
            rabbitmq.publish_message(
                os.getenv("MAIL_DEAD_QUEUE", "email_dead_letter"),
                {
                    "event_type": "mail.quarantined",
                    "event_version": 1,
                    "reason": type(exc).__name__,
                    "original": body.decode(errors="replace"),
                },
            )
            try:
                event_id, payload_hash = normalize(json.loads(body), properties.message_id)
                conn = connect()
                try:
                    with conn, conn.cursor() as cur:
                        cur.execute(
                            "UPDATE mail_event SET state='dead',last_error=%s "
                            "WHERE id=%s AND payload_hash=%s AND state!='delivered'",
                            (type(exc).__name__, event_id, payload_hash),
                        )
                finally:
                    conn.close()
            except (ValueError, TypeError, KeyError):
                pass
            ch.basic_ack(delivery_tag=method.delivery_tag)
            outcome = "quarantined"
        finally:
            logger.info(
                json.dumps(
                    {
                        "component": "email-worker",
                        "outcome": outcome,
                        "latency_ms": round((time.monotonic() - started) * 1000, 3),
                    }
                )
            )

    def start_consuming(self):
        delay = 1
        while True:
            connection = None
            try:
                connection = rabbitmq.get_connection()
                ch = connection.channel()
                queue = os.getenv("MAIL_QUEUE", "email_queue")
                ch.queue_declare(queue=queue, durable=True)
                ch.basic_qos(prefetch_count=1)
                while connection.is_open:
                    dispatch_one(rabbitmq, queue)
                    method, properties, body = ch.basic_get(queue=queue, auto_ack=False)
                    if method:
                        self.process_email_task(ch, method, properties, body)
                    connection.process_data_events(time_limit=0.2)
                    delay = 1
                    if not method:
                        time.sleep(0.2)
            except KeyboardInterrupt:
                return
            except Exception as exc:
                logger.warning(
                    json.dumps(
                        {
                            "component": "email-worker",
                            "outcome": "dependency_error",
                            "error": type(exc).__name__,
                            "backoff_seconds": delay,
                        }
                    )
                )
                time.sleep(delay)
                delay = min(30, delay * 2)
            finally:
                if connection is not None and connection.is_open:
                    connection.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    EmailWorker().start_consuming()
