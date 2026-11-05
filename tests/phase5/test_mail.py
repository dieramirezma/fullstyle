"""Actual SQL/RabbitMQ receipts, rollback, legacy compatibility and re-delivery."""

import json
import os
import subprocess
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from config.rabbitmq_config import rabbitmq
from services.durable_mail import connect, dispatch_one, normalize, persist
from workers.email_worker import EmailWorker

if os.getenv("PHASE5_MUTATION") == "mail-atomic":
    import services.durable_mail as durable_mail

    original_record = durable_mail.record_delivery

    def broken_record(result):
        value = original_record(result)
        durable_mail.delivery_context.get()[0].commit()
        return value

    durable_mail.record_delivery = broken_record


class MailTests(unittest.TestCase):
    def message(self, kind="contact", version=1):
        message = {
            "event_id": uuid4().hex,
            "email_type": kind,
            "data": {
                "name": "Synthetic",
                "email": "test@synthetic.invalid",
                "message": "synthetic request",
            },
        }
        if version:
            message.update(event_type="mail.requested", event_version=version)
        return message

    def state(self, event_id):
        conn = connect()
        try:
            with conn, conn.cursor() as cur:
                cur.execute("SELECT state FROM mail_event WHERE id=%s", (event_id,))
                state = cur.fetchone()["state"]
                cur.execute(
                    "SELECT count(*) AS count FROM mail_delivery WHERE event_id=%s",
                    (event_id,),
                )
                return state, cur.fetchone()["count"]
        finally:
            conn.close()

    def test_01_legacy_and_versioned_events_and_concurrent_duplicates(self):
        for version in (0, 1):
            message = self.message(version=version)
            with ThreadPoolExecutor(max_workers=4) as pool:
                outcomes = list(
                    pool.map(lambda _: EmailWorker().deliver(message), range(4))
                )
            self.assertEqual(outcomes.count("delivered"), 1)
            self.assertEqual(outcomes.count("duplicate"), 3)
            # A contact has two distinct deliveries; neither may be lost or duplicated.
            self.assertEqual(self.state(message["event_id"]), ("delivered", 2))
            changed = {
                **message,
                "data": {**message["data"], "email": "other@synthetic.invalid"},
            }
            with self.assertRaises(ValueError):
                EmailWorker().deliver(changed)
            self.assertEqual(self.state(message["event_id"]), ("delivered", 2))

    def test_02_failure_between_contact_deliveries_rolls_back_and_recovers(self):
        message = self.message()
        worker = EmailWorker()
        original = worker.email_service.send_email
        calls = 0

        def fail_second(*args):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("controlled failure before second local receipt")
            return original(*args)

        worker.email_service.send_email = fail_second
        with self.assertRaises(OSError):
            worker.deliver(message)
        self.assertEqual(self.state(message["event_id"]), ("pending", 0))
        self.assertEqual(EmailWorker().deliver(message), "delivered")
        self.assertEqual(self.state(message["event_id"]), ("delivered", 2))

    def test_03_broker_redelivers_after_process_exit_before_ack(self):
        message = self.message()
        queue = os.environ["MAIL_QUEUE"] + "_redelivery"
        rabbitmq.publish_message(queue, message)
        code = """
import json,os
from config.rabbitmq_config import rabbitmq
from workers.email_worker import EmailWorker
c=rabbitmq.get_connection();ch=c.channel()
m,p,b=ch.basic_get(queue=os.environ['CRASH_QUEUE'],auto_ack=False)
assert m is not None
assert EmailWorker().deliver(json.loads(b))=='delivered'
os._exit(73)
"""
        result = subprocess.run(
            [sys.executable, "-c", code],
            env={**os.environ, "CRASH_QUEUE": queue},
            timeout=15,
        )
        self.assertEqual(result.returncode, 73)
        conn = rabbitmq.get_connection()
        try:
            ch = conn.channel()
            method, props, body = ch.basic_get(queue=queue, auto_ack=False)
            self.assertIsNotNone(method)
            self.assertTrue(method.redelivered)
            self.assertEqual(
                EmailWorker().deliver(json.loads(body), props.message_id), "duplicate"
            )
            ch.basic_ack(method.delivery_tag)
            self.assertEqual(self.state(message["event_id"]), ("delivered", 2))
            ch.queue_delete(queue=queue)
        finally:
            conn.close()

    def test_04_poison_message_is_confirmed_in_dead_letter_queue(self):
        conn = rabbitmq.get_connection()
        try:
            ch = conn.channel()
            queue = os.environ["MAIL_QUEUE"] + "_poison"
            dead = os.environ["MAIL_DEAD_QUEUE"]
            for body in (b'{"event_version":99}', b"not-json"):
                ch.queue_declare(queue=queue, durable=True)
                ch.basic_publish("", queue, body)
                method, props, received = ch.basic_get(queue=queue, auto_ack=False)
                EmailWorker().process_email_task(ch, method, props, received)
                ch.queue_declare(queue=dead, durable=True)
                dm, _, db = ch.basic_get(queue=dead, auto_ack=True)
                self.assertIsNotNone(dm)
                self.assertEqual(json.loads(db)["event_type"], "mail.quarantined")
                self.assertIsNone(ch.basic_get(queue=queue, auto_ack=True)[0])
            ch.queue_delete(queue=queue)
        finally:
            conn.close()

    def test_05_broker_failure_keeps_intent_and_backs_off(self):
        message = self.message()
        persist(message)
        # Earlier pending cases must not change which event the dispatcher selects.
        conn = connect()
        with conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE mail_event SET next_attempt=now()+interval '1 day' WHERE id!=%s",
                (message["event_id"],),
            )
        conn.close()

        class Unavailable:
            def publish_message(self, *args):
                raise ConnectionError("controlled broker failure")

        self.assertTrue(dispatch_one(Unavailable(), os.environ["MAIL_QUEUE"]))
        self.assertEqual(self.state(message["event_id"]), ("pending", 0))
        conn = connect()
        with conn, conn.cursor() as cur:
            cur.execute(
                "SELECT attempts,last_error,next_attempt>now() AS backed_off FROM mail_event WHERE id=%s",
                (message["event_id"],),
            )
            result = cur.fetchone()
        conn.close()
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(result["last_error"], "ConnectionError")
        self.assertTrue(result["backed_off"])

    def test_06_normalize_rejects_unknown_versions(self):
        for value in (True, -1, 2, "1", None):
            with self.assertRaises(ValueError):
                normalize(self.message(version=value) | {"event_version": value})

    def test_07_colliding_poison_cannot_retire_a_valid_pending_intent(self):
        original = self.message()
        persist(original)
        altered = {**original, "data": {**original["data"], "message": "different"}}
        queue = os.environ["MAIL_QUEUE"] + "_collision"
        rabbitmq.publish_message(queue, altered)
        conn = rabbitmq.get_connection()
        try:
            ch = conn.channel()
            method, props, body = ch.basic_get(queue=queue, auto_ack=False)
            self.assertIsNotNone(method)
            EmailWorker().process_email_task(ch, method, props, body)
            self.assertEqual(self.state(original["event_id"]), ("pending", 0))
            self.assertEqual(EmailWorker().deliver(original), "delivered")
            self.assertEqual(self.state(original["event_id"]), ("delivered", 2))
            ch.queue_delete(queue=queue)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
