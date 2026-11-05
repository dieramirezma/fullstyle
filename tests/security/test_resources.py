"""Real Flask requests and PostgreSQL persistence, with a disposable schema."""

import importlib
import unittest
import uuid
from datetime import datetime
from unittest.mock import patch

import psycopg2
from config.db_config import db
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from flask_restful import Api


class ResourceAuthorizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = "phase2_" + uuid.uuid4().hex
        cls.uri = (
            "postgresql://synthetic:local-synthetic-only@postgres/fullstyle_synthetic"
        )
        cls.admin = psycopg2.connect(cls.uri)
        cls.admin.autocommit = True
        with cls.admin.cursor() as cursor:
            cursor.execute("CREATE SCHEMA " + cls.schema)
        # Models use the independent db extension, never the production app factory.
        for name in (
            "user",
            "client",
            "manager",
            "site",
            "category",
            "service",
            "worker",
            "detail",
            "appointment",
            "availability",
            "days_off",
            "seasonal_schedule",
            "worker_has_service",
            "site_has_category",
            "payment",
            "notification",
        ):
            importlib.import_module("models." + name + "_model")
        from services.appointment_service import (
            Appointment,
            AppointmentDetail,
            AppointmentSiteStatistics,
        )
        from services.cache_service import CacheClear
        from services.identity_service import CurrentUser
        from services.log_service import GetLogs
        from services.notification_service import Notification
        from services.payment_service import Payment
        from services.site_service import Site
        from services.user_service import Enable2FA, RegisterGoogle, User, UserRegister
        from services.worker_service import Worker

        cls.app = Flask(__name__)
        cls.app.config.update(
            TESTING=True,
            JWT_SECRET_KEY="synthetic-test-secret-with-32-characters",
            SQLALCHEMY_DATABASE_URI=cls.uri,
            SQLALCHEMY_ENGINE_OPTIONS={
                "connect_args": {"options": "-csearch_path=" + cls.schema}
            },
        )
        db.init_app(cls.app)
        JWTManager(cls.app)
        api = Api(cls.app)
        api.add_resource(User, "/api/user/<int:id>")
        api.add_resource(UserRegister, "/api/register")
        api.add_resource(RegisterGoogle, "/api/register_google")
        api.add_resource(Enable2FA, "/api/enable-2fa")
        api.add_resource(CurrentUser, "/api/me")
        api.add_resource(Site, "/api/site")
        api.add_resource(Worker, "/api/worker")
        api.add_resource(Payment, "/api/payment")
        api.add_resource(Notification, "/api/notification")
        api.add_resource(CacheClear, "/api/cache/clear")
        api.add_resource(GetLogs, "/api/logs")
        api.add_resource(Appointment, "/api/appointment")
        api.add_resource(AppointmentDetail, "/api/appointmentdetail")
        api.add_resource(AppointmentSiteStatistics, "/api/appointment/site_statistics")
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.session.remove()
            db.engine.dispose()
        with cls.admin.cursor() as cursor:
            cursor.execute("DROP SCHEMA " + cls.schema + " CASCADE")
        cls.admin.close()

    def setUp(self):
        from models.appointment_model import AppointmentModel
        from models.category_model import CategoryModel
        from models.manager_model import ManagerModel
        from models.service_model import ServiceModel
        from models.site_model import SiteModel
        from models.user_model import UserModel
        from models.worker_model import WorkerModel

        self.context = self.app.app_context()
        self.context.push()
        db.drop_all()
        db.create_all()
        users = [
            UserModel(
                email=f"u{i}@synthetic.invalid", name=f"u{i}", password="unchanged-hash"
            )
            for i in range(1, 5)
        ]
        db.session.add_all(users)
        db.session.flush()
        self.a, self.b, self.owner, self.other_owner = [u.id for u in users]
        for user in users[2:]:
            db.session.add(
                ManagerModel(
                    bankaccount=123,
                    accounttype="test",
                    bankentity="test",
                    userModel=user,
                )
            )
        self.site = SiteModel(
            id=1,
            name="synthetic",
            address="test",
            phone=None,
            manager_id=self.owner,
            photos=[],
        )
        db.session.add(self.site)
        db.session.add(
            SiteModel(
                id=2,
                name="other",
                address="test",
                phone=None,
                manager_id=self.other_owner,
                photos=[],
            )
        )
        db.session.flush()
        worker = WorkerModel(name="worker", site_id=1)
        category = CategoryModel(name="test")
        db.session.add(category)
        db.session.flush()
        service = ServiceModel(category_id=category.id, name="test")
        db.session.add_all([worker, service])
        db.session.flush()
        from models.detail_model import DetailModel

        db.session.add(
            DetailModel(
                site_id=1,
                service_id=service.id,
                description="test",
                price=1000,
                duration=30,
                photos=[],
            )
        )
        self.worker, self.service = worker.id, service.id
        appointment = AppointmentModel(
            appointmenttime=datetime(2030, 1, 1, 10),
            status="pending",
            worker_id=worker.id,
            site_id=1,
            service_id=service.id,
            client_id=self.b,
        )
        db.session.add(appointment)
        db.session.commit()
        self.appointment = appointment.id
        self.tokens = {u.id: create_access_token(identity=str(u.id)) for u in users}

    def tearDown(self):
        db.session.remove()
        self.context.pop()

    def call(self, method, path, actor=None, **kwargs):
        headers = {"Authorization": "Bearer " + self.tokens[actor]} if actor else {}
        return getattr(self.client, method)(path, headers=headers, **kwargs)

    def payload(self, **changes):
        return dict(
            id=self.appointment,
            appointmenttime="2030-01-01T10:00:00",
            worker_id=self.worker,
            site_id=1,
            service_id=self.service,
            client_id=self.b,
            status="pending",
            **changes,
        )

    def test_cross_user_read_update_delete_rejected_and_data_unchanged(self):
        from models.user_model import UserModel

        for method in ("get", "put", "delete"):
            with self.subTest(method=method):
                response = self.call(
                    method,
                    f"/api/user/{self.b}",
                    self.a,
                    json={
                        "name": "attacker",
                        "email": "attacker@synthetic.invalid",
                        "password": "password123",
                    },
                )
                self.assertEqual(response.status_code, 403)
                db.session.expire_all()
                victim = UserModel.find_by_id(self.b)
                self.assertEqual(victim.name, "u2")
                self.assertEqual(victim.password, "unchanged-hash")

    def test_own_user_and_unauthenticated_access(self):
        self.assertEqual(
            self.call("get", f"/api/user/{self.a}", self.a).status_code, 200
        )
        self.assertEqual(self.call("get", f"/api/user/{self.a}").status_code, 401)

    def test_identity_management_cannot_restore_or_configure_another_account(self):
        from models.user_model import UserModel
        from werkzeug.security import generate_password_hash

        user = UserModel.find_by_id(self.b)
        user.active = False
        user.password = generate_password_hash("original-secret-password")
        db.session.commit()
        response = self.client.post(
            "/api/register",
            json={
                "name": "victim",
                "email": "u2@synthetic.invalid",
                "password": "wrong-password",
            },
        )
        self.assertEqual(response.status_code, 401)
        db.session.expire_all()
        self.assertFalse(db.session.get(UserModel, self.b).active)
        self.assertEqual(
            self.call(
                "post",
                "/api/enable-2fa",
                self.a,
                json={"email": "u2@synthetic.invalid"},
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                "/api/register_google",
                json={"name": "test", "email": "u1@synthetic.invalid"},
            ).status_code,
            400,
        )

    def test_appointment_lists_and_detail_do_not_expose_other_clients(self):
        for path in ("/api/appointment", "/api/appointmentdetail"):
            with self.subTest(path=path):
                response = self.call("get", path, self.a)
                self.assertEqual(response.status_code, 404)
                self.assertNotIn("client_id", response.get_json())
        response = self.call("get", "/api/appointment", self.b)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([r["id"] for r in response.get_json()], [self.appointment])

    def test_other_client_cannot_create_update_or_delete_victims_booking(self):
        from models.appointment_model import AppointmentModel

        for method in ("post", "put", "delete"):
            with self.subTest(method=method):
                response = self.call(
                    method,
                    "/api/appointment?id=" + str(self.appointment),
                    self.a,
                    json=self.payload(),
                )
                self.assertIn(response.status_code, (403, 404))
                db.session.expire_all()
                self.assertEqual(AppointmentModel.query.count(), 1)
                self.assertEqual(
                    AppointmentModel.find_by_id(self.appointment).client_id, self.b
                )

    def test_owner_can_read_own_site_but_other_owner_cannot(self):
        self.assertEqual(
            self.call("get", "/api/appointment", self.owner).status_code, 200
        )
        self.assertEqual(
            self.call("get", "/api/appointment", self.other_owner).status_code, 404
        )
        self.assertEqual(
            self.call(
                "get", "/api/appointment/site_statistics?site_id=1", self.other_owner
            ).status_code,
            403,
        )

    def test_booking_client_cannot_be_reassigned(self):
        payload = self.payload()
        payload["client_id"] = self.a
        with patch(
            "services.appointment_service.is_worker_available",
            return_value=(True, None),
        ):
            response = self.call("put", "/api/appointment", self.b, json=payload)
        self.assertEqual(response.status_code, 403)
        from models.appointment_model import AppointmentModel

        db.session.expire_all()
        self.assertEqual(
            AppointmentModel.find_by_id(self.appointment).client_id, self.b
        )

    def test_inactive_user_token_rejected(self):
        from models.user_model import UserModel

        user = UserModel.find_by_id(self.a)
        user.active = False
        db.session.commit()
        self.assertEqual(self.call("get", "/api/appointment", self.a).status_code, 401)

    def test_go_shaped_access_tokens_remain_compatible_and_refresh_is_denied(self):
        import time

        import jwt
        from flask_jwt_extended import create_refresh_token

        now = int(time.time())
        token = jwt.encode(
            {
                "sub": str(self.a),
                "type": "access",
                "fresh": False,
                "iat": now,
                "nbf": now,
                "exp": now + 60,
                "jti": uuid.uuid4().hex,
                "csrf": uuid.uuid4().hex,
            },
            self.app.config["JWT_SECRET_KEY"],
            algorithm="HS256",
        )
        response = self.client.get(
            "/api/me", headers={"Authorization": "Bearer " + token}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["id"], self.a)
        refresh = create_refresh_token(identity=str(self.a))
        self.assertEqual(
            self.client.get(
                "/api/me", headers={"Authorization": "Bearer " + refresh}
            ).status_code,
            422,
        )

    def test_authorized_create_update_and_validation_only_have_expected_effects(self):
        from models.appointment_model import AppointmentModel

        payload = self.payload()
        payload["client_id"] = self.a
        payload["id"] = None
        payload["request"] = 1
        with patch(
            "services.appointment_service.is_worker_available",
            return_value=(True, None),
        ):
            response = self.call("post", "/api/appointment", self.a, json=payload)
            self.assertEqual(response.status_code, 200)
            self.assertIs(response.get_json(), True)
            self.assertEqual(AppointmentModel.query.count(), 1)
            payload["request"] = 0
            response = self.call("post", "/api/appointment", self.a, json=payload)
            self.assertEqual(response.status_code, 201)
            payload["id"] = response.get_json()["id"]
            payload["status"] = "cancelled"
            response = self.call("put", "/api/appointment", self.a, json=payload)
            self.assertEqual(response.status_code, 200)
        db.session.expire_all()
        self.assertEqual(AppointmentModel.find_by_id(payload["id"]).status, "cancelled")

    def test_owner_client_can_delete_own_booking(self):
        from models.appointment_model import AppointmentModel

        self.assertEqual(
            self.call(
                "delete", "/api/appointment?id=" + str(self.appointment), self.b
            ).status_code,
            200,
        )
        self.assertIsNone(AppointmentModel.find_by_id(self.appointment))

    def test_site_ownership_cannot_be_stolen_and_worker_delete_cannot_cascade(self):
        from models.appointment_model import AppointmentModel
        from models.site_model import SiteModel

        response = self.call(
            "put",
            "/api/site?id=1",
            self.other_owner,
            json={"manager_id": self.other_owner},
        )
        self.assertEqual(response.status_code, 403)
        response = self.call(
            "delete", "/api/worker?id=" + str(self.worker), self.other_owner
        )
        self.assertEqual(response.status_code, 403)
        db.session.expire_all()
        self.assertEqual(SiteModel.query.filter_by(id=1).first().manager_id, self.owner)
        self.assertIsNotNone(AppointmentModel.find_by_id(self.appointment))

    def test_payment_and_notification_cannot_reference_foreign_appointment(self):
        for route, payload in [
            ("/api/payment", {"amount": 1, "paymentmethod": "synthetic"}),
            ("/api/notification", {"type": "synthetic"}),
        ]:
            with self.subTest(route=route):
                response = self.call(
                    "post",
                    route,
                    self.a,
                    json=dict(payload, appointment_id=self.appointment),
                )
                self.assertEqual(response.status_code, 404)
        from models.notification_model import NotificationModel
        from models.payment_model import PaymentModel

        self.assertEqual(PaymentModel.query.count(), 0)
        self.assertEqual(NotificationModel.query.count(), 0)

    def test_operational_routes_cannot_flush_shared_redis_or_expose_logs(self):
        self.assertEqual(
            self.call("delete", "/api/cache/clear", self.a).status_code, 403
        )
        self.assertEqual(self.call("get", "/api/logs", self.a).status_code, 403)
        self.assertEqual(self.call("delete", "/api/cache/clear").status_code, 401)

    def test_chatbot_delegates_and_denies_cross_user_write_with_real_database(self):
        import json

        import httpx
        from app.api.v1.endpoints import chat_handler
        from app.infrastructure.clients.business_logic_client import BusinessLogicClient
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from models.appointment_model import AppointmentModel

        original = httpx.AsyncClient
        sessions = []

        def backend(request):
            body = json.loads(request.content) if request.content else None
            response = self.client.open(
                request.url.path
                + ("?" + request.url.query.decode() if request.url.query else ""),
                method=request.method,
                headers={"Authorization": request.headers.get("Authorization", "")},
                json=body,
            )
            return httpx.Response(
                response.status_code,
                content=response.data,
                headers={"Content-Type": "application/json"},
            )

        def factory(**kwargs):
            return original(transport=httpx.MockTransport(backend), **kwargs)

        class Agent:
            async def generate_text_with_agent(
                agent, user_input, session_id, history=None
            ):
                sessions.append(session_id)
                result = await BusinessLogicClient().delete_appointment(
                    self.appointment
                )
                return json.dumps(result)

        class IsolatedConversation:
            """This test isolates delegation; phase 5 tests the real SQL store separately."""

            replayed = False

            def __init__(conversation, *args):
                pass

            def begin(conversation):
                return None, []

            def complete(conversation, reply):
                return None

            def close(conversation):
                return None

        app = FastAPI()
        app.include_router(chat_handler.router, prefix="/api/v1/chat")
        with (
            patch("httpx.AsyncClient", side_effect=factory),
            patch.object(chat_handler, "get_llm_service", return_value=Agent()),
            patch.object(chat_handler, "Conversation", IsolatedConversation),
        ):
            with TestClient(app) as client:
                body = {"message": "delete booking", "session_id": "shared-session"}
                anonymous = client.post("/api/v1/chat/send", json=body)
                self.assertEqual(anonymous.status_code, 401)
                denied = client.post(
                    "/api/v1/chat/send",
                    json=body,
                    headers={"Authorization": "Bearer " + self.tokens[self.a]},
                )
                self.assertEqual(denied.status_code, 200)
                self.assertEqual(json.loads(denied.json()["reply"])["status_code"], 404)
                db.session.expire_all()
                self.assertIsNotNone(AppointmentModel.find_by_id(self.appointment))
                allowed = client.post(
                    "/api/v1/chat/send",
                    json=body,
                    headers={"Authorization": "Bearer " + self.tokens[self.b]},
                )
                self.assertEqual(allowed.status_code, 200)
                self.assertEqual(
                    json.loads(allowed.json()["reply"])["message"],
                    "Appointment deleted",
                )
        db.session.expire_all()
        self.assertIsNone(AppointmentModel.find_by_id(self.appointment))
        self.assertEqual(
            sessions, [f"{self.a}:shared-session", f"{self.b}:shared-session"]
        )
