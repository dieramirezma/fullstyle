"""Real PostgreSQL transactions/independent connections and disposable real Redis.

The runner supplies only the isolated local DB and an expendable Redis instance.
Mutations below affect only in-memory functions in the test process.
"""

import hashlib
import importlib
import json
import os
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from datetime import time as clock
from unittest.mock import patch
from uuid import uuid4

import jwt
import psycopg2
import redis
from config.db_config import db
from config.server_config import create_app
from flask_jwt_extended import create_access_token
from models.appointment_model import AppointmentModel
from models.availability_model import AvailabilityModel
from models.category_model import CategoryModel
from models.consistency_model import (
    BookingTerms,
    ProviderTransaction,
)
from models.detail_model import DetailModel
from models.manager_model import ManagerModel
from models.payment_model import PaymentModel
from models.service_model import ServiceModel
from models.session_model import ProviderReceipt
from models.site_model import SiteModel
from models.user_model import UserModel
from models.worker_model import WorkerModel
from services.integration_service import canonical
from sqlalchemy import event, text
from sqlalchemy.exc import OperationalError

URI = "postgresql://synthetic:local-synthetic-only@postgres/fullstyle_synthetic"


class ConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("DATABASE_URL") != URI or not os.environ[
            "PHASE4_REDIS"
        ].startswith("phase4-redis-"):
            raise RuntimeError("Explicit synthetic DB and expendable Redis required")
        cls.schema = "phase4_" + uuid4().hex
        cls.admin = psycopg2.connect(URI)
        cls.admin.autocommit = True
        with cls.admin.cursor() as cursor:
            cursor.execute("CREATE SCHEMA " + cls.schema)
        cls.addClassCleanup(cls.cleanup)
        cls.app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_ENGINE_OPTIONS": {
                    "pool_size": 12,
                    "max_overflow": 0,
                    "connect_args": {"options": "-csearch_path=" + cls.schema},
                },
            }
        )
        import utils.cache_helper as cache

        cls.redis = redis.Redis(
            host=os.environ["PHASE4_REDIS"],
            decode_responses=True,
            socket_timeout=0.3,
            socket_connect_timeout=0.3,
        )
        cls.cache_patch = patch.object(cache, "redis_client", cls.redis)
        cls.cache_patch.start()
        cls.addClassCleanup(cls.cache_patch.stop)
        if os.getenv("PHASE4_MUTATION") == "worker-lock":
            cls.mutation = patch(
                "services.appointment_service.lock_workers", lambda *args: None
            )
            cls.mutation.start()
            cls.addClassCleanup(cls.mutation.stop)
        if os.getenv("PHASE4_MUTATION") == "cache-status":
            # Emulate the original cache bug: hit returns decoded [body, status] as body/200.
            original_get = cls.redis.get

            def broken_get(key):
                value = original_get(key)
                if value:
                    body = json.loads(value)
                    body["body"] = [body["body"], body["status"]]
                    body["status"] = 200
                    return json.dumps(body)
                return value

            cls.mutation = patch.object(cls.redis, "get", broken_get)
            cls.mutation.start()
            cls.addClassCleanup(cls.mutation.stop)

    @classmethod
    def cleanup(cls):
        if hasattr(cls, "app"):
            with cls.app.app_context():
                db.session.remove()
                db.engine.dispose()
        with cls.admin.cursor() as cursor:
            cursor.execute("DROP SCHEMA " + cls.schema + " CASCADE")
        cls.admin.close()

    def setUp(self):
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            users = [
                UserModel(
                    email=f"{uuid4().hex}@synthetic.invalid",
                    name="test",
                    password="unused",
                )
                for _ in range(3)
            ]
            db.session.add_all(users)
            db.session.flush()
            self.actor, self.other, self.manager = [u.id for u in users]
            db.session.add(
                ManagerModel(
                    bankaccount=1,
                    accounttype="test",
                    bankentity="test",
                    userModel=users[2],
                )
            )
            db.session.flush()
            db.session.add(
                SiteModel(
                    id=1,
                    name="test",
                    address="test",
                    phone=None,
                    manager_id=self.manager,
                    photos=[],
                )
            )
            category = CategoryModel(name="test")
            db.session.add(category)
            db.session.flush()
            service = ServiceModel(category_id=category.id, name="test")
            db.session.add(service)
            db.session.flush()
            self.service = service.id
            for i in (1, 2):
                worker = WorkerModel(name="worker", site_id=1)
                worker.id = i
                db.session.add(worker)
            db.session.flush()
            db.session.add(
                DetailModel(
                    site_id=1,
                    service_id=self.service,
                    price=1000,
                    duration=30,
                    description="test",
                    photos=[],
                )
            )
            for worker_id in (1, 2):
                db.session.add(
                    AvailabilityModel(
                        worker_id=worker_id,
                        weekday="Tuesday",
                        starttime=clock(8),
                        endtime=clock(18),
                    )
                )
            db.session.commit()
            self.tokens = {u.id: create_access_token(identity=str(u.id)) for u in users}

    def call(self, method, path="/api/appointment", actor=None, **kwargs):
        with self.app.test_client() as client:
            return getattr(client, method)(
                path,
                headers={"Authorization": "Bearer " + self.tokens[actor or self.actor]},
                **kwargs,
            )

    def booking(self, **changes):
        return {
            "appointmenttime": "2030-01-01T10:00:00",
            "status": "pending",
            "worker_id": 1,
            "site_id": 1,
            "service_id": self.service,
            "client_id": self.actor,
            **changes,
        }

    def create(self, **changes):
        response = self.call("post", json=self.booking(**changes))
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()

    def intent(self, appointment_id):
        response = self.call(
            "post",
            "/api/payment",
            json={
                "amount": 1000,
                "status": "pending",
                "paymentmethod": "wompi",
                "appointment_id": appointment_id,
            },
        )
        self.assertIn(response.status_code, (200, 201), response.get_json())
        return response.get_json()

    def provider_event(
        self,
        reference=None,
        identifier=None,
        status="APPROVED",
        amount=100000,
        currency="COP",
        properties=None,
    ):
        transaction = {
            "id": identifier or uuid4().hex,
            "status": status,
            "amount_in_cents": amount,
        }
        if reference is not None:
            transaction.update(reference=reference, currency=currency)
        return {
            "event": "transaction.updated",
            "environment": "test",
            "timestamp": int(time.time()),
            "data": {"transaction": transaction},
            "signature": {
                "properties": properties
                or ["transaction." + key for key in transaction]
            },
        }

    def webhook(self, body):
        values = []
        for path in body["signature"]["properties"]:
            value = body["data"]
            for part in path.split("."):
                value = value[part]
            values.append(str(value))
        checksum = hashlib.sha256(
            (
                "".join(values)
                + str(body["timestamp"])
                + os.environ["WOMPI_EVENTS_KEY"]
            ).encode()
        ).hexdigest()
        encoded = canonical(body).encode()
        now = int(time.time())
        capability = jwt.encode(
            {
                "sub": "fullstyle-next",
                "type": "service",
                "aud": "wompi.receipt",
                "iat": now,
                "exp": now + 60,
                "jti": uuid4().hex,
                "sha256": hashlib.sha256(encoded).hexdigest(),
            },
            os.environ["INTEGRATION_SECRET"],
            algorithm="HS256",
        )
        with self.app.test_client() as client:
            return client.post(
                "/api/integrations/wompi/events",
                data=encoded,
                content_type="application/json",
                headers={
                    "X-Event-Checksum": checksum,
                    "Authorization": "Bearer " + capability,
                },
            )

    def race(self, calls):
        barrier = threading.Barrier(len(calls))

        def invoke(call):
            barrier.wait(timeout=10)
            return call()

        with ThreadPoolExecutor(max_workers=len(calls)) as executor:
            return list(executor.map(invoke, calls))

    def test_01_concurrent_creates_one_winner_independent_connections(self):
        module = importlib.import_module("services.appointment_service")
        original = module.is_worker_available
        pids = []

        def delayed(*args, **kwargs):
            available = original(*args, **kwargs)
            pids.append(db.session.execute(text("select pg_backend_pid()")).scalar())
            time.sleep(
                0.12
            )  # Opens the unsafe check/write gap in the no-lock mutation.
            return available

        with patch.object(module, "is_worker_available", delayed):
            responses = self.race(
                [lambda: self.call("post", json=self.booking()) for _ in range(6)]
            )
        self.assertEqual(
            sorted(r.status_code for r in responses), [201, 409, 409, 409, 409, 409]
        )
        self.assertEqual(len(set(pids)), 6)
        with self.app.app_context():
            self.assertEqual(AppointmentModel.query.count(), 1)
            self.assertEqual(BookingTerms.query.count(), 1)

    def test_02_concurrent_updates_and_create_compete_for_same_slot(self):
        appointments = [
            self.create(appointmenttime=f"2030-01-01T{hour:02}:00:00")
            for hour in (8, 9, 11, 12)
        ]
        calls = [
            lambda a=a: self.call("put", json=self.booking(id=a["id"]))
            for a in appointments
        ]
        calls.append(lambda: self.call("post", json=self.booking()))
        responses = self.race(calls)
        self.assertEqual(sum(r.status_code in (200, 201) for r in responses), 1)
        self.assertEqual(sum(r.status_code == 409 for r in responses), 4)
        with self.app.app_context():
            self.assertEqual(
                AppointmentModel.query.filter_by(
                    appointmenttime=datetime(2030, 1, 1, 10)
                ).count(),
                1,
            )

    def test_03_worker_move_conflict_rolls_back_and_old_slot_can_be_reused(self):
        first = self.create()
        other = self.create(worker_id=2)
        rejected = self.call("put", json=self.booking(id=first["id"], worker_id=2))
        self.assertEqual(rejected.status_code, 409)
        with self.app.app_context():
            self.assertEqual(db.session.get(AppointmentModel, first["id"]).worker_id, 1)
        self.assertEqual(
            self.call("delete", "/api/appointment?id=" + str(other["id"])).status_code,
            200,
        )
        self.assertEqual(
            self.call(
                "put", json=self.booking(id=first["id"], worker_id=2)
            ).status_code,
            200,
        )
        self.create()

    def test_04_interval_boundaries_snapshot_and_cancelled_slots(self):
        first = self.create()
        with self.app.app_context():
            DetailModel.query.first().duration = 5
            DetailModel.query.first().price = 9999
            db.session.commit()
        self.assertEqual(
            self.call(
                "post", json=self.booking(appointmenttime="2030-01-01T10:15:00")
            ).status_code,
            409,
        )
        self.create(appointmenttime="2030-01-01T10:30:00")
        self.assertEqual(
            self.call(
                "put", json=self.booking(id=first["id"], status="cancelled")
            ).status_code,
            200,
        )
        self.create()
        self.assertEqual(
            self.call(
                "post", json=self.booking(appointmenttime="2030-01-01T17:59:00")
            ).status_code,
            400,
        )
        with self.app.app_context():
            self.assertEqual(db.session.get(BookingTerms, first["id"]).amount, 1000)

    def test_05_cache_hit_miss_exact_body_status_scope_and_invalidation(self):
        category_miss, category_hit = (
            self.call("get", "/api/category"),
            self.call("get", "/api/category"),
        )
        self.assertEqual(
            (category_hit.status_code, category_hit.get_json()),
            (category_miss.status_code, category_miss.get_json()),
        )
        first = self.call("get")
        second = self.call("get")
        self.assertEqual(first.status_code, 404)
        self.assertEqual(
            (second.status_code, second.get_json()),
            (first.status_code, first.get_json()),
        )
        appointment = self.create()
        miss, hit = self.call("get"), self.call("get")
        self.assertEqual(
            (hit.status_code, hit.get_json()), (miss.status_code, miss.get_json())
        )
        self.assertEqual(hit.get_json()[0]["id"], appointment["id"])
        self.assertEqual(self.call("get", actor=self.other).status_code, 404)
        self.assertEqual(
            self.call(
                "put",
                json=self.booking(
                    id=appointment["id"], appointmenttime="2030-01-01T11:00:00"
                ),
            ).status_code,
            200,
        )
        self.assertIn("11:00:00", self.call("get").get_json()[0]["appointmenttime"])
        self.assertEqual(
            self.call(
                "delete", "/api/appointment?id=" + str(appointment["id"])
            ).status_code,
            200,
        )
        self.assertEqual(self.call("get").status_code, 404)

    def test_06_cache_failure_never_reexecutes_business_logic_or_changes_error(self):
        from utils.cache_helper import cache_result

        calls = []

        @cache_result(namespace="categories")
        def business():
            calls.append(1)
            return {"message": "gone"}, 404

        with (
            self.app.test_request_context("/test"),
            patch.object(self.redis, "setex", side_effect=redis.ConnectionError),
        ):
            self.assertEqual(business(), ({"message": "gone"}, 404))
        self.assertEqual(len(calls), 1)

    def test_07_payment_terms_and_subscription_cannot_be_supplied_by_clients(self):
        self.assertEqual(
            self.call("post", json=self.booking(status="paid")).status_code, 403
        )
        appointment = self.create()
        for status, amount, expected in (("paid", 1000, 403), ("pending", 1, 400)):
            response = self.call(
                "post",
                "/api/payment",
                json={
                    "amount": amount,
                    "status": status,
                    "paymentmethod": "wompi",
                    "appointment_id": appointment["id"],
                },
            )
            self.assertEqual(response.status_code, expected)
        self.assertEqual(
            self.call(
                "put",
                f"/api/subscription/{self.manager}",
                actor=self.manager,
                json={"subscriptionactive": True, "subscriptiontype": "Premium"},
            ).status_code,
            403,
        )
        with self.app.app_context():
            self.assertFalse(
                db.session.get(ManagerModel, self.manager).subscriptionactive
            )
            self.assertEqual(PaymentModel.query.count(), 0)
        intent = self.intent(appointment["id"])
        self.assertEqual(intent["amount_in_cents"], 100000)
        self.assertEqual(
            self.intent(appointment["id"])["reference"], intent["reference"]
        )
        self.assertEqual(
            self.call("put", json=self.booking(id=appointment["id"])).status_code, 409
        )
        self.assertEqual(
            self.call("delete", "/api/payment?id=" + str(intent["id"])).status_code, 403
        )

    def test_08_concurrent_repeated_webhooks_apply_exactly_once(self):
        appointment = self.create()
        intent = self.intent(appointment["id"])
        body = self.provider_event(reference=intent["reference"])
        responses = self.race([lambda: self.webhook(body) for _ in range(6)])
        self.assertEqual([r.status_code for r in responses], [202] * 6)
        results = [r.get_json() for r in responses]
        self.assertEqual(len({r["receipt_id"] for r in results}), 1)
        self.assertEqual(sum(not r["duplicate"] for r in results), 1)
        with self.app.app_context():
            self.assertEqual(ProviderReceipt.query.count(), 1)
            self.assertEqual(
                ProviderTransaction.query.filter(
                    ProviderTransaction.applied_payment_id.is_not(None)
                ).count(),
                1,
            )
            self.assertEqual(PaymentModel.query.filter_by(status="paid").count(), 1)
            self.assertEqual(
                db.session.get(AppointmentModel, appointment["id"]).status, "paid"
            )

    def test_09_signed_mismatch_unsigned_reference_and_foreign_identity_do_not_apply(
        self,
    ):
        appointment = self.create()
        intent = self.intent(appointment["id"])
        for body, expected in (
            (self.provider_event(reference=intent["reference"], amount=1), 409),
            (self.provider_event(reference=intent["reference"], currency="USD"), 409),
            (
                self.provider_event(
                    reference=intent["reference"],
                    properties=[
                        "transaction.id",
                        "transaction.status",
                        "transaction.amount_in_cents",
                    ],
                ),
                401,
            ),
        ):
            response = self.webhook(body)
            self.assertEqual(response.status_code, expected)
            self.assertTrue(response.is_json)
            self.assertTrue(response.get_json()["message"])
        self.assertEqual(
            self.call(
                "post",
                "/api/payment",
                actor=self.other,
                json={
                    "amount": 1000,
                    "paymentmethod": "wompi",
                    "appointment_id": appointment["id"],
                },
            ).status_code,
            404,
        )
        with self.app.app_context():
            self.assertEqual(ProviderReceipt.query.count(), 0)
            self.assertEqual(PaymentModel.query.first().status, "pending")

    def test_10_pending_approved_stale_and_transaction_identity_conflicts(self):
        appointment = self.create()
        intent = self.intent(appointment["id"])
        body = self.provider_event(reference=intent["reference"], status="PENDING")
        self.assertFalse(self.webhook(body).get_json()["payment_applied"])
        body["data"]["transaction"]["status"] = "APPROVED"
        self.assertTrue(self.webhook(body).get_json()["payment_applied"])
        body["data"]["transaction"]["status"] = "PENDING"
        self.assertTrue(self.webhook(body).get_json()["duplicate"])
        body["data"]["transaction"]["amount_in_cents"] = 200000
        self.assertEqual(self.webhook(body).status_code, 409)
        second = self.provider_event(reference=intent["reference"])
        self.assertEqual(self.webhook(second).status_code, 409)
        with self.app.app_context():
            self.assertEqual(ProviderReceipt.query.count(), 1)
            self.assertEqual(ProviderTransaction.query.first().status, "APPROVED")

    def test_11_settlement_failure_rolls_back_receipt_booking_payment_and_retry(self):
        appointment = self.create()
        intent = self.intent(appointment["id"])
        body = self.provider_event(reference=intent["reference"])

        def reject_commit(session):
            raise OperationalError(
                "controlled commit failure", None, Exception("synthetic")
            )

        with self.app.app_context():
            session_type = type(db.session())
        event.listen(session_type, "before_commit", reject_commit)
        try:
            self.assertEqual(self.webhook(body).status_code, 503)
        finally:
            event.remove(session_type, "before_commit", reject_commit)
        with self.app.app_context():
            self.assertEqual(ProviderReceipt.query.count(), 0)
            self.assertEqual(PaymentModel.query.first().status, "pending")
            self.assertEqual(AppointmentModel.query.first().status, "pending")
        self.assertTrue(self.webhook(body).get_json()["payment_applied"])

    def test_12_cache_racing_writer_cannot_publish_stale_value_in_new_generation(self):
        from utils.cache_helper import cache_result

        read, write = threading.Event(), threading.Event()

        @cache_result(namespace="appointments", private=True)
        def slow_read():
            result = [a.json() for a in AppointmentModel.query.all()], 200
            read.set()
            self.assertTrue(write.wait(10))
            return result

        def old_reader():
            with self.app.test_request_context(
                "/api/appointment",
                headers={"Authorization": "Bearer " + self.tokens[self.actor]},
            ):
                from flask_jwt_extended import verify_jwt_in_request

                verify_jwt_in_request()
                return slow_read()

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(old_reader)
            self.assertTrue(read.wait(10))
            self.create()
            write.set()
            self.assertEqual(future.result()[0], [])
        self.assertEqual(len(old_reader()[0]), 1)
        self.assertEqual(len(self.call("get").get_json()), 1)

    def test_13_different_transactions_cannot_settle_the_same_intent_twice(self):
        appointment = self.create()
        intent = self.intent(appointment["id"])
        bodies = [self.provider_event(reference=intent["reference"]) for _ in range(2)]
        responses = self.race([lambda body=body: self.webhook(body) for body in bodies])
        self.assertEqual(sorted(r.status_code for r in responses), [202, 409])
        with self.app.app_context():
            self.assertEqual(ProviderReceipt.query.count(), 1)
            self.assertEqual(ProviderTransaction.query.count(), 1)
            self.assertEqual(PaymentModel.query.filter_by(status="paid").count(), 1)

    def test_14_long_and_cross_midnight_legacy_intervals_cannot_be_hidden_by_nearest_booking(
        self,
    ):
        with self.app.app_context():
            for when, duration in (
                (datetime(2030, 1, 1, 9), 180),
                (datetime(2030, 1, 1, 10), 5),
                (datetime(2029, 12, 31, 23), 600),
            ):
                appointment = AppointmentModel(
                    appointmenttime=when,
                    status="pending",
                    worker_id=1,
                    site_id=1,
                    service_id=self.service,
                    client_id=self.actor,
                )
                db.session.add(appointment)
                db.session.flush()
                db.session.add(
                    BookingTerms(
                        appointment_id=appointment.id,
                        duration=duration,
                        amount=1000,
                        currency="COP",
                    )
                )
            db.session.commit()
        for when in ("2030-01-01T08:30:00", "2030-01-01T11:00:00"):
            self.assertEqual(
                self.call("post", json=self.booking(appointmenttime=when)).status_code,
                409,
            )

    def test_15_lock_timeout_is_controlled_and_retry_does_not_leave_a_booking(self):
        blocker = psycopg2.connect(URI, options="-csearch_path=" + self.schema)
        try:
            with blocker.cursor() as cursor:
                cursor.execute("SELECT id FROM worker WHERE id=1 FOR UPDATE")
            self.assertEqual(self.call("post", json=self.booking()).status_code, 409)
        finally:
            blocker.rollback()
            blocker.close()
        with self.app.app_context():
            self.assertEqual(AppointmentModel.query.count(), 0)
            self.assertEqual(BookingTerms.query.count(), 0)
        self.create()

    def test_16_unknown_reference_is_deduplicated_without_financial_effect(self):
        body = self.provider_event(reference=str(uuid4()))
        first = self.webhook(body)
        second = self.webhook(body)
        self.assertEqual((first.status_code, second.status_code), (202, 202))
        self.assertFalse(first.get_json()["payment_applied"])
        self.assertTrue(second.get_json()["duplicate"])
        self.assertEqual(
            first.get_json()["receipt_id"], second.get_json()["receipt_id"]
        )
        with self.app.app_context():
            self.assertEqual(PaymentModel.query.count(), 0)
            self.assertEqual(ProviderTransaction.query.count(), 1)

    def test_99_real_redis_shutdown_writes_and_settlement_still_use_postgres(self):
        appointment = self.create()
        self.call("get")
        try:
            self.redis.shutdown(nosave=True)
        except redis.ConnectionError:
            pass
        self.assertEqual(
            self.call(
                "put",
                json=self.booking(
                    id=appointment["id"], appointmenttime="2030-01-01T11:00:00"
                ),
            ).status_code,
            200,
        )
        response = self.call("get")
        self.assertEqual(response.status_code, 200)
        self.assertIn("11:00:00", response.get_json()[0]["appointmenttime"])
        self.assertEqual(
            self.call(
                "post", json=self.booking(appointmenttime="2030-01-01T11:00:00")
            ).status_code,
            409,
        )
        intent = self.intent(appointment["id"])
        body = self.provider_event(reference=intent["reference"])
        self.assertTrue(self.webhook(body).get_json()["payment_applied"])
        self.assertTrue(self.webhook(body).get_json()["duplicate"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
