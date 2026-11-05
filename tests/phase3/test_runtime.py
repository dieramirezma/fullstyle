"""Real HTTP across Nginx/Next/GraphQL/Go/Flask/chat and local data services.

Run only through run_phase3.py after stack validation. No mocks or original DB.
"""

import base64
import hashlib
import json
import os
import time
import unittest
from datetime import datetime, timedelta
from datetime import time as clock
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

import jwt
import redis
import requests
from config.db_config import db
from config.server_config import create_app
from models.appointment_model import AppointmentModel
from models.availability_model import AvailabilityModel
from models.category_model import CategoryModel
from models.consistency_model import PaymentIntent
from models.detail_model import DetailModel
from models.manager_model import ManagerModel
from models.payment_model import PaymentModel
from models.service_model import ServiceModel
from models.session_model import IdentityLink, ProviderReceipt, RevokedToken
from models.site_model import SiteModel
from models.user_model import UserModel
from models.worker_model import WorkerModel

ORIGIN = "http://proxy"
PASSWORD = "Synthetic-password-32!"
SECRET = "synthetic-phase3-jwt-signing-key-32bytes-minimum"


class RuntimeContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if (
            os.getenv("DATABASE_URL")
            != "postgresql://synthetic:local-synthetic-only@postgres/fullstyle_synthetic"
        ):
            raise RuntimeError("Only isolated synthetic database accepted")
        cls.prefix = "phase3_" + uuid4().hex
        cls.http = requests.Session()
        cls.http.trust_env = False
        cls.app = create_app()
        cls.user_ids = []
        cls.receipts = []
        cls.firebase_tokens = []
        cls.accounts = []
        cls.site_id = cls.worker_id = cls.service_id = cls.category_id = None
        cls.addClassCleanup(cls.cleanup)
        for issuer, suffix in (
            ("business", "flask"),
            ("auth", "go"),
            ("business", "other"),
            ("business", "reset"),
        ):
            email = f"{cls.prefix}_{suffix}@synthetic.invalid"
            response = cls.http.post(
                ORIGIN + f"/{issuer}/api/register",
                json={
                    "name": cls.prefix + suffix,
                    "email": email,
                    "password": PASSWORD,
                },
                timeout=10,
            )
            if response.status_code != 200:
                raise AssertionError(
                    "Registration failed at "
                    + issuer
                    + ": "
                    + str(response.status_code)
                    + " "
                    + response.text[:300]
                )
            result = response.json()
            cls.accounts.append(
                (
                    email,
                    result["access_token"],
                    result["refresh_token"],
                    result["user"]["id"],
                )
            )
            cls.user_ids.append(result["user"]["id"])
        with cls.app.app_context():
            user = db.session.get(UserModel, cls.user_ids[2])
            manager = ManagerModel(
                bankaccount=123, accounttype="local", bankentity="local", userModel=user
            )
            db.session.add(manager)
            db.session.flush()
            site = SiteModel(
                id=None,
                name=cls.prefix,
                address="Synthetic",
                phone="123",
                manager_id=user.id,
                photos=[],
            )
            db.session.add(site)
            db.session.flush()
            worker = WorkerModel(name=cls.prefix, site_id=site.id)
            category = CategoryModel(name=cls.prefix)
            db.session.add_all([worker, category])
            db.session.flush()
            service = ServiceModel(category_id=category.id, name=cls.prefix)
            db.session.add(service)
            db.session.flush()
            db.session.add(
                DetailModel(
                    site_id=site.id,
                    service_id=service.id,
                    description="Synthetic",
                    price=1000,
                    duration=30,
                    photos=[],
                )
            )
            for day in (
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ):
                db.session.add(
                    AvailabilityModel(
                        worker_id=worker.id,
                        weekday=day,
                        starttime=clock(8),
                        endtime=clock(18),
                    )
                )
            db.session.commit()
            cls.site_id, cls.worker_id, cls.service_id, cls.category_id = (
                site.id,
                worker.id,
                service.id,
                category.id,
            )

    @classmethod
    def cleanup(cls):
        with cls.app.app_context():
            # Delete only this run's rows, using known IDs; never drop/truncate tables.
            ProviderReceipt.query.filter(ProviderReceipt.id.in_(cls.receipts)).delete()
            booking_ids = db.select(AppointmentModel.id).where(
                AppointmentModel.worker_id == cls.worker_id
            )
            PaymentIntent.query.filter(
                PaymentIntent.appointment_id.in_(booking_ids)
            ).delete(synchronize_session=False)
            PaymentModel.query.filter(
                PaymentModel.appointment_id.in_(booking_ids)
            ).delete(synchronize_session=False)
            AppointmentModel.query.filter(
                AppointmentModel.worker_id == cls.worker_id
            ).delete()
            AvailabilityModel.query.filter_by(worker_id=cls.worker_id).delete()
            DetailModel.query.filter_by(site_id=cls.site_id).delete()
            WorkerModel.query.filter_by(id=cls.worker_id).delete()
            SiteModel.query.filter_by(id=cls.site_id).delete()
            ServiceModel.query.filter_by(id=cls.service_id).delete()
            CategoryModel.query.filter_by(id=cls.category_id).delete()
            IdentityLink.query.filter(IdentityLink.user_id.in_(cls.user_ids)).delete()
            RevokedToken.query.filter(
                RevokedToken.subject.in_([str(x) for x in cls.user_ids])
            ).delete()
            ManagerModel.query.filter(ManagerModel.id.in_(cls.user_ids)).delete()
            from models.client_model import ClientModel

            ClientModel.query.filter(ClientModel.id.in_(cls.user_ids)).delete()
            ProviderReceipt.query.filter(ProviderReceipt.id.in_(cls.receipts)).delete()
            UserModel.query.filter(UserModel.id.in_(cls.user_ids)).delete()
            db.session.commit()
            db.session.remove()
            db.engine.dispose()
        for token in cls.firebase_tokens:
            cls.http.post(
                "http://firebase:9099/identitytoolkit.googleapis.com/v1/accounts:delete?key=local",
                json={"idToken": token},
                timeout=5,
            )
        outbox = redis.Redis(host="redis", db=2)
        for key in ("local-mail-outbox", "local-reset-outbox"):
            for entry in outbox.lrange(key, 0, -1):
                if cls.prefix.encode() in entry:
                    outbox.lrem(key, 0, entry)
        cls.http.close()

    def call(self, method, path, expected, token=None, **kwargs):
        headers = kwargs.pop("headers", {})
        if token:
            headers["Authorization"] = "Bearer " + token
        response = self.http.request(
            method, ORIGIN + path, headers=headers, timeout=15, **kwargs
        )
        self.assertEqual(
            response.status_code,
            expected,
            f"{method} {path}: {response.status_code}, {response.text[:180]}",
        )
        return response

    def test_01_routes_health_and_correlation(self):
        for path in (
            "/health",
            "/business/health",
            "/business/ready",
            "/auth/health",
            "/auth/ready",
            "/chatbot/health",
            "/api/health",
            "/mail/ready",
        ):
            with self.subTest(path=path):
                response = self.call(
                    "GET",
                    path,
                    200,
                    headers={
                        "X-Correlation-ID": "phase3-trace",
                        "X-Operation-ID": "phase3-op",
                    },
                )
                self.assertEqual(response.headers["X-Correlation-ID"], "phase3-trace")
                self.assertEqual(response.headers["X-Operation-ID"], "phase3-op")
        self.call("GET", "/login", 200)
        self.call("GET", "/business/api/swagger.json", 200)
        self.call("GET", "/api/logic/me", 401)

    def test_02_legacy_hashes_cross_issuer(self):
        for index, issuer in ((0, "auth"), (1, "business")):
            email, _, _, user_id = self.accounts[index]
            with self.app.app_context():
                before = db.session.get(UserModel, user_id).password
            response = self.call(
                "POST",
                f"/{issuer}/api/login",
                200,
                json={"email": email, "password": PASSWORD},
            ).json()
            access = response.get("access_token", response.get("token"))
            self.assertEqual(
                self.call("GET", "/business/api/me", 200, access).json()["id"], user_id
            )
            self.call(
                "POST",
                f"/{issuer}/api/login",
                401,
                json={"email": email, "password": "wrong-password"},
            )
            with self.app.app_context():
                self.assertEqual(db.session.get(UserModel, user_id).password, before)

    def test_03_rotation_expiry_and_independent_revocation(self):
        email = self.accounts[0][0]
        sessions = [
            self.call(
                "POST",
                "/auth/api/login",
                200,
                json={"email": email, "password": PASSWORD},
            ).json()
            for _ in range(2)
        ]
        claims = [
            jwt.decode(x["token"], SECRET, algorithms=["HS256"]) for x in sessions
        ]
        self.assertNotEqual(claims[0]["jti"], claims[1]["jti"])
        self.call("DELETE", "/business/api/logout", 200, sessions[0]["token"])
        self.call("GET", "/business/api/me", 401, sessions[0]["token"])
        self.call("GET", "/business/api/me", 200, sessions[1]["token"])
        self.call("GET", "/business/api/me", 422, sessions[1]["refresh_token"])
        refreshed = self.call(
            "POST", "/business/api/refresh", 200, sessions[1]["refresh_token"]
        ).json()
        self.call("POST", "/business/api/refresh", 401, sessions[1]["refresh_token"])
        self.call("GET", "/business/api/me", 200, refreshed["access_token"])
        access_claims = jwt.decode(
            refreshed["access_token"], SECRET, algorithms=["HS256"]
        )
        refresh_claims = jwt.decode(
            refreshed["refresh_token"], SECRET, algorithms=["HS256"]
        )
        self.assertLessEqual(access_claims["exp"] - access_claims["iat"], 3600)
        self.assertLessEqual(refresh_claims["exp"] - refresh_claims["iat"], 15 * 86400)
        self.call("DELETE", "/business/api/logout", 200, refreshed["refresh_token"])
        self.call("POST", "/business/api/refresh", 401, refreshed["refresh_token"])
        expired = {**claims[1], "exp": int(time.time()) - 1, "jti": uuid4().hex}
        self.call(
            "GET",
            "/business/api/me",
            401,
            jwt.encode(expired, SECRET, algorithm="HS256"),
        )

    def test_04_graphql_and_chat_resource_policy(self):
        _, token, _, user_id = self.accounts[0]
        self.call(
            "POST",
            "/graphql",
            200,
            token,
            json={
                "query": "query($id:Int!){getUser(id:$id){id active}}",
                "variables": {"id": user_id},
            },
        )
        denied = self.call(
            "POST",
            "/graphql",
            200,
            token,
            json={
                "query": "query($id:Int!){getUser(id:$id){id active}}",
                "variables": {"id": self.user_ids[1]},
            },
        ).json()
        self.assertTrue(denied.get("errors"))
        when = (
            (datetime.now() + timedelta(days=2))
            .replace(hour=10, minute=0, second=0, microsecond=0)
            .isoformat()
        )
        input_data = {
            "appointmenttime": when,
            "worker_id": self.worker_id,
            "site_id": self.site_id,
            "service_id": self.service_id,
            "client_id": user_id,
        }
        created = self.call(
            "POST",
            "/graphql",
            200,
            token,
            json={
                "query": "mutation($input:AppointmentInput!){createAppointment(input:$input){status message}}",
                "variables": {"input": input_data},
            },
        ).json()
        self.assertFalse(created.get("errors"), created)
        self.assertTrue(created["data"]["createAppointment"]["status"])
        with self.app.app_context():
            appointment = AppointmentModel.query.filter_by(
                worker_id=self.worker_id, client_id=user_id
            ).one()
            booking_id = appointment.id
        self.call(
            "POST",
            "/chatbot/api/v1/chat/send",
            401,
            json={"message": f"cancelar {booking_id}"},
        )
        result = self.call(
            "POST",
            "/graphql",
            200,
            self.accounts[1][1],
            json={
                "query": "mutation($message:String!,$session_id:String){sendMessage(message:$message,session_id:$session_id){reply session_id}}",
                "variables": {
                    "message": f"cancelar {booking_id}",
                    "session_id": "same",
                },
            },
        ).json()
        self.assertFalse(result.get("errors"), result)
        self.assertIn("404", result["data"]["sendMessage"]["reply"])
        with self.app.app_context():
            self.assertIsNotNone(db.session.get(AppointmentModel, booking_id))
        self.call(
            "POST",
            "/chatbot/api/v1/chat/send",
            200,
            token,
            json={"message": f"cancelar {booking_id}", "session_id": "same"},
        )
        with self.app.app_context():
            self.assertIsNone(db.session.get(AppointmentModel, booking_id))

    def test_05_next_provider_boundaries_and_mail_delivery(self):
        token = self.accounts[1][1]
        for path in (
            "/api/UploadMedia",
            "/api/wompi",
            "/api/recaptcha",
            "/api/sendEmail/contact",
        ):
            self.call("POST", path, 401, json={})
        self.call("GET", "/api/geocode?address=synthetic", 401)
        self.call("POST", "/api/wompi", 503, token, json={"amount": 1})
        self.call(
            "POST",
            "/mail/api/emails/contact",
            401,
            token,
            json={"email": "victim@synthetic.invalid"},
        )
        response = self.call(
            "POST",
            "/api/sendEmail/contact",
            202,
            token,
            json={"message": self.prefix, "email": "victim@synthetic.invalid"},
        )
        self.assertIn("queued", response.json()["message"])
        outbox = redis.Redis(host="redis", db=2)
        expected_email = self.accounts[1][0]
        for _ in range(40):
            entries = [json.loads(v) for v in outbox.lrange("local-mail-outbox", 0, 99)]
            if any(expected_email in entry["to"] for entry in entries):
                break
            time.sleep(0.25)
        else:
            self.fail("RabbitMQ worker did not deliver the synthetic confirmation")
        self.assertFalse(
            any("victim@synthetic.invalid" in entry["to"] for entry in entries)
        )
        owned = [
            entry
            for entry in entries
            if expected_email in entry["to"] or entry.get("requester") == expected_email
        ]
        self.assertEqual(
            len(owned), 2, "Contact must produce support delivery and requester reply"
        )

    def test_06_upload_size_type_and_owner(self):
        token = self.accounts[0][1]
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/l9sAAAAASUVORK5CYII="
        )
        uploaded = self.call(
            "POST",
            "/api/UploadMedia",
            200,
            token,
            files={"image": ("tiny.png", png, "image/png")},
        ).json()
        self.assertEqual(self.call("GET", uploaded["url"], 200, token).content, png)
        self.call("GET", uploaded["url"], 404, self.accounts[1][1])
        self.call(
            "POST",
            "/api/UploadMedia",
            400,
            token,
            files={"image": ("fake.png", b"<svg>bad</svg>", "image/png")},
        )
        self.call(
            "POST",
            "/api/UploadMedia",
            413,
            token,
            files={"image": ("big.png", png + b"x" * 1100000, "image/png")},
        )

    def test_07_webhook_receipt_without_booking_commands(self):
        body = {
            "event": "transaction.updated",
            "environment": "test",
            "timestamp": int(time.time()),
            "data": {
                "transaction": {
                    "id": self.prefix,
                    "status": "APPROVED",
                    "amount_in_cents": 10000,
                    "reference": "SUB_other_user_untrusted",
                }
            },
            "signature": {
                "properties": [
                    "transaction.id",
                    "transaction.status",
                    "transaction.amount_in_cents",
                ]
            },
        }
        checksum = hashlib.sha256(
            f"{self.prefix}APPROVED10000{body['timestamp']}synthetic-wompi-events-local-only".encode()
        ).hexdigest()
        self.call("POST", "/api/wompi/webhook", 400, json=body)
        self.call(
            "POST",
            "/api/wompi/webhook",
            401,
            json=body,
            headers={"X-Event-Checksum": "0" * 64},
        )
        received = self.call(
            "POST",
            "/api/wompi/webhook",
            202,
            json=body,
            headers={"X-Event-Checksum": checksum},
        ).json()
        self.receipts.append(received["receipt_id"])
        self.assertFalse(received["payment_applied"])
        with self.app.app_context():
            receipt = db.session.get(ProviderReceipt, received["receipt_id"])
            self.assertEqual(receipt.transaction_id, self.prefix)
            self.assertEqual(receipt.state, "received")
        body["data"]["transaction"]["amount_in_cents"] = 99999
        self.call(
            "POST",
            "/api/wompi/webhook",
            401,
            json=body,
            headers={"X-Event-Checksum": checksum},
        )
        self.call(
            "POST",
            "/business/api/integrations/wompi/events",
            401,
            self.accounts[0][1],
            json=body,
        )

    def test_08_firebase_link_requires_both_proofs(self):
        proof = self.http.post(
            "http://firebase:9099/identitytoolkit.googleapis.com/v1/accounts:signUp?key=local",
            json={
                "email": f"{self.prefix}@synthetic.invalid",
                "password": PASSWORD,
                "returnSecureToken": True,
            },
            timeout=10,
        )
        self.assertEqual(proof.status_code, 200)
        firebase_token = proof.json()["idToken"]
        self.__class__.firebase_uid = proof.json()["localId"]
        self.firebase_tokens.append(firebase_token)
        body = {"firebase_token": firebase_token}
        self.call("POST", "/business/api/identity/firebase/session", 403, json=body)
        self.call(
            "POST",
            "/business/api/identity/firebase/link",
            401,
            self.accounts[0][1],
            json={**body, "password": "wrong"},
        )
        self.call(
            "POST",
            "/business/api/identity/firebase/link",
            201,
            self.accounts[0][1],
            json={**body, "password": PASSWORD},
        )
        self.call(
            "POST",
            "/business/api/identity/firebase/link",
            409,
            self.accounts[1][1],
            json={**body, "password": PASSWORD},
        )
        session = self.call(
            "POST", "/business/api/identity/firebase/session", 200, json=body
        ).json()
        self.assertEqual(session["user"]["id"], self.user_ids[0])
        self.__class__.firebase_sql_token = session["access_token"]
        self.call("GET", "/business/api/me", 200, session["access_token"])
        self.call(
            "POST",
            "/business/api/identity/firebase/session",
            401,
            json={"firebase_token": "forged-uid-is-not-proof"},
        )

    def test_09_reset_token_is_single_purpose_and_single_use(self):
        email, access, _, _ = self.accounts[3]
        self.call(
            "POST",
            "/business/api/user/reset-password-request",
            200,
            json={"email": email},
        )
        from models.reliability_model import MailEvent

        with self.app.app_context():
            events = MailEvent.query.filter(
                MailEvent.payload["data"]["email"].as_string() == email
            ).all()
            self.assertEqual(len(events), 1)
            item = events[0].payload["data"]
        reset = parse_qs(urlsplit(item["reset_link"]).query)["token"][0]
        self.call("GET", "/business/api/me", 401, reset)
        self.call(
            "POST",
            "/business/api/user/reset-password",
            400,
            json={"token": access, "password": "new-synthetic-password"},
        )
        self.call(
            "POST",
            "/business/api/user/reset-password",
            200,
            json={"token": reset, "password": "new-synthetic-password"},
        )
        self.call(
            "POST",
            "/business/api/user/reset-password",
            400,
            json={"token": reset, "password": "other-synthetic-password"},
        )
        for issuer in ("business", "auth"):
            self.call(
                "POST",
                f"/{issuer}/api/login",
                200,
                json={"email": email, "password": "new-synthetic-password"},
            )

    def test_10_revoked_and_inactive_identity_cannot_reach_providers(self):
        _, access, _, user_id = self.accounts[2]
        with self.app.app_context():
            user = db.session.get(UserModel, user_id)
            user.active = False
            db.session.commit()
        try:
            self.call("GET", "/business/api/me", 401, access)
            self.call("POST", "/api/UploadMedia", 401, access, json={})
            self.call(
                "POST",
                "/auth/api/login",
                401,
                json={"email": self.accounts[2][0], "password": PASSWORD},
            )
        finally:
            with self.app.app_context():
                db.session.get(UserModel, user_id).active = True
                db.session.commit()

    def test_11_nextauth_cookie_login_and_signout_revoke_its_pair(self):
        browser = requests.Session()
        browser.trust_env = False
        browser.headers["Host"] = urlsplit(
            os.getenv("APP_WEB_URL", "http://localhost:38080")
        ).netloc
        try:
            csrf = browser.get(ORIGIN + "/api/auth/csrf", timeout=10).json()[
                "csrfToken"
            ]
            response = browser.post(
                ORIGIN + "/api/auth/callback/credentials",
                data={
                    "csrfToken": csrf,
                    "email": self.accounts[1][0],
                    "password": PASSWORD,
                    "json": "true",
                    "callbackUrl": os.getenv("APP_WEB_URL", "http://localhost:38080/"),
                },
                timeout=15,
            )
            self.assertEqual(response.status_code, 200)
            session = browser.get(ORIGIN + "/api/auth/session", timeout=10).json()
            self.assertEqual(
                session.get("user", {}).get("id"), self.user_ids[1], session
            )
            self.assertTrue(session["accessToken"])
            self.assertNotIn("refreshToken", session["user"])
            self.assertNotIn("token", session["user"])
            self.call("GET", "/business/api/me", 200, session["accessToken"])
            self.assertEqual(
                browser.get(
                    ORIGIN + "/api/geocode?address=synthetic", timeout=10
                ).status_code,
                503,
            )
            csrf = browser.get(ORIGIN + "/api/auth/csrf", timeout=10).json()[
                "csrfToken"
            ]
            response = browser.post(
                ORIGIN + "/api/auth/signout",
                data={"csrfToken": csrf, "json": "true"},
                timeout=15,
            )
            self.assertEqual(response.status_code, 200)
            self.assertFalse(
                browser.get(ORIGIN + "/api/auth/session", timeout=10).json()
            )
            self.call("GET", "/business/api/me", 401, session["accessToken"])
            self.call("GET", "/business/api/me", 200, self.accounts[1][1])
        finally:
            browser.close()

    def test_12_shared_legacy_go_jti_is_revoked_only_for_its_subject(self):
        tokens = []
        for user_id in self.user_ids[:2]:
            tokens.append(
                jwt.encode(
                    {
                        "sub": str(user_id),
                        "type": "access",
                        "jti": "legacy-shared-identifier",
                        "iat": int(time.time()),
                        "nbf": int(time.time()),
                        "exp": int(time.time()) + 60,
                        "fresh": False,
                    },
                    SECRET,
                    algorithm="HS256",
                )
            )
        self.call("DELETE", "/business/api/logout", 200, tokens[0])
        self.call("GET", "/business/api/me", 401, tokens[0])
        self.call("GET", "/business/api/me", 200, tokens[1])

    def test_13_provider_quota_is_enforced_before_any_external_use(self):
        for _ in range(42):
            response = self.http.post(
                ORIGIN + "/business/api/provider/authorize",
                json={"action": "geocode"},
                headers={"Authorization": "Bearer " + self.accounts[2][1]},
                timeout=5,
            )
            self.assertIn(response.status_code, (200, 429))
            if response.status_code == 429:
                break
        else:
            self.fail("Per-identity provider quota was not enforced")

    def test_14_disabled_firebase_identity_invalidates_exchanged_sql_access(self):
        from services.session_service import local_firebase_auth

        proof = self.http.post(
            "http://firebase:9099/identitytoolkit.googleapis.com/v1/accounts:signUp?key=local",
            json={
                "email": f"{self.prefix}_revoked@synthetic.invalid",
                "password": PASSWORD,
                "returnSecureToken": True,
            },
            timeout=10,
        )
        self.assertEqual(proof.status_code, 200)
        firebase_token = proof.json()["idToken"]
        firebase_uid = proof.json()["localId"]
        self.firebase_tokens.append(firebase_token)
        access = self.call(
            "POST",
            "/business/api/login",
            200,
            json={"email": self.accounts[1][0], "password": PASSWORD},
        ).json()["access_token"]
        self.call(
            "POST",
            "/business/api/identity/firebase/link",
            201,
            access,
            json={"firebase_token": firebase_token, "password": PASSWORD},
        )
        firebase_sql_token = self.call(
            "POST",
            "/business/api/identity/firebase/session",
            200,
            json={"firebase_token": firebase_token},
        ).json()["access_token"]
        self.call("GET", "/business/api/me", 200, firebase_sql_token)
        admin = local_firebase_auth()
        admin.update_user(firebase_uid, disabled=True)
        try:
            self.call(
                "POST",
                "/business/api/identity/firebase/session",
                401,
                json={"firebase_token": firebase_token},
            )
            self.call("GET", "/business/api/me", 401, firebase_sql_token)
            self.call("GET", "/business/api/me", 200, access)
        finally:
            admin.update_user(firebase_uid, disabled=False)

    def test_15_legacy_scrypt_hash_remains_unchanged_across_both_issuers(self):
        from werkzeug.security import generate_password_hash

        encoded = generate_password_hash(PASSWORD, method="scrypt")
        with self.app.app_context():
            db.session.get(UserModel, self.user_ids[3]).password = encoded
            db.session.commit()
        for issuer in ("business", "auth"):
            self.call(
                "POST",
                f"/{issuer}/api/login",
                200,
                json={"email": self.accounts[3][0], "password": PASSWORD},
            )
        with self.app.app_context():
            self.assertEqual(
                db.session.get(UserModel, self.user_ids[3]).password, encoded
            )

    def test_16_local_payment_intent_graphql_and_repeated_next_webhook(self):
        token = self.accounts[0][1]
        payload = {
            "appointmenttime": "2031-01-01T10:00:00",
            "status": "pending",
            "worker_id": self.worker_id,
            "site_id": self.site_id,
            "service_id": self.service_id,
            "client_id": self.user_ids[0],
        }
        appointment = self.call(
            "POST", "/business/api/appointment", 201, token, json=payload
        ).json()
        path = "/business/api/appointment?id=" + str(appointment["id"])
        before = self.call("GET", path, 200, token).json()
        self.assertEqual(self.call("GET", path, 200, token).json(), before)
        result = self.call(
            "POST",
            "/graphql",
            200,
            token,
            json={
                "query": "mutation ($input: PaymentInput!) { createPayment(input:$input) { id reference amount_in_cents currency status } }",
                "variables": {
                    "input": {
                        "amount": 1000,
                        "paymentmethod": "wompi",
                        "status": "pending",
                        "appointment_id": appointment["id"],
                    }
                },
            },
        ).json()
        self.assertNotIn("errors", result)
        intent = result["data"]["createPayment"]
        self.assertEqual(intent["amount_in_cents"], 100000)
        transaction = {
            "id": self.prefix + "_settled",
            "status": "APPROVED",
            "amount_in_cents": 100000,
            "currency": "COP",
            "reference": intent["reference"],
        }
        body = {
            "event": "transaction.updated",
            "environment": "test",
            "timestamp": int(time.time()),
            "data": {"transaction": transaction},
            "signature": {"properties": ["transaction." + key for key in transaction]},
        }
        checksum = hashlib.sha256(
            (
                "".join(str(value) for value in transaction.values())
                + str(body["timestamp"])
                + "synthetic-wompi-events-local-only"
            ).encode()
        ).hexdigest()
        mismatch = json.loads(json.dumps(body))
        mismatch["data"]["transaction"]["amount_in_cents"] = 1
        mismatch_checksum = hashlib.sha256(
            (
                "".join(
                    str(value) for value in mismatch["data"]["transaction"].values()
                )
                + str(body["timestamp"])
                + "synthetic-wompi-events-local-only"
            ).encode()
        ).hexdigest()
        rejected = self.call(
            "POST",
            "/api/wompi/webhook",
            409,
            json=mismatch,
            headers={"X-Event-Checksum": mismatch_checksum},
        ).json()
        self.assertTrue(rejected["message"])
        first = self.call(
            "POST",
            "/api/wompi/webhook",
            202,
            json=body,
            headers={"X-Event-Checksum": checksum},
        ).json()
        self.receipts.append(first["receipt_id"])
        self.assertTrue(first["payment_applied"])
        self.assertFalse(first["duplicate"])
        repeated = self.call(
            "POST",
            "/api/wompi/webhook",
            202,
            json=body,
            headers={"X-Event-Checksum": checksum},
        ).json()
        self.assertEqual(repeated["receipt_id"], first["receipt_id"])
        self.assertTrue(repeated["duplicate"])
        after = self.call("GET", path, 200, token).json()
        self.assertEqual(after[0]["status"], "paid")
        self.assertEqual(self.call("GET", path, 200, token).json(), after)
        with self.app.app_context():
            self.assertEqual(db.session.get(PaymentModel, intent["id"]).status, "paid")
            self.assertEqual(
                ProviderReceipt.query.filter_by(
                    transaction_id=transaction["id"]
                ).count(),
                1,
            )

    def test_17_go_registration_does_not_grant_client_subscription(self):
        result = self.call(
            "POST",
            "/auth/api/manager_register",
            200,
            json={
                "name": self.prefix,
                "email": self.prefix + "_manager@synthetic.invalid",
                "password": PASSWORD,
                "bankaccount": 1,
                "accounttype": "synthetic",
                "bankentity": "synthetic",
                "subscriptionactive": True,
                "subscriptiontype": "Premium",
                "subscriptionstartdate": "2030-01-01T00:00:00Z",
                "subscriptionfinishdate": "2031-01-01T00:00:00Z",
            },
        ).json()
        user_id = result["user"]["id"]
        self.user_ids.append(user_id)
        with self.app.app_context():
            manager = db.session.get(ManagerModel, user_id)
            self.assertFalse(manager.subscriptionactive)
            self.assertEqual(manager.subscriptiontype, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
