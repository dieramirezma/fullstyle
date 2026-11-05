"""MFA across real proxy, GraphQL/Go, NextAuth and Firebase emulator."""

import json
import math
import os
import time
from pathlib import Path
from uuid import uuid4

import pyotp
import requests
from config.db_config import db
from config.server_config import create_app
from migrate_local import EXPECTED
from models.account_security_model import AccountSecurity
from sqlalchemy import text
from utils.account_security import cipher


def main():
    if os.getenv("DATABASE_URL") != EXPECTED or os.getenv("LOCAL_RUNTIME") != "true":
        raise RuntimeError("Only the isolated synthetic DB is allowed")
    app = create_app()
    http = requests.Session()
    http.trust_env = False
    origin = "http://proxy"
    password = "Synthetic-password-32!"
    users, firebase_tokens, completed = [], [], []
    timings = {"login": [], "identity_read": []}
    budgets = json.loads(Path("/tests/local-budgets.json").read_text())["contracts"]

    def request(method, path, status, token=None, **kwargs):
        started = time.perf_counter()
        response = http.request(
            method,
            origin + path,
            headers={"Authorization": "Bearer " + token} if token else {},
            timeout=12,
            **kwargs,
        )
        assert response.status_code == status, (
            path,
            response.status_code,
            response.text[:200],
        )
        kind = (
            "login"
            if path.endswith("/login")
            else "identity_read"
            if path.endswith("/me")
            else None
        )
        if kind:
            timings[kind].append((time.perf_counter() - started) * 1000)
        return response.json()

    def account(issuer="business"):
        email = "phase6_" + uuid4().hex + "@synthetic.invalid"
        data = {"name": "Synthetic", "email": email, "password": password}
        result = request("POST", f"/{issuer}/api/register", 200, json=data)
        users.append(result["user"]["id"])
        return data, result

    def seed_mfa(user_id):
        secret = pyotp.random_base32()
        with app.app_context():
            state = db.session.get(AccountSecurity, user_id)
            if state is None:
                state = AccountSecurity(user_id=user_id)
                db.session.add(state)
            state.enabled = True
            state.epoch = 1
            state.secret = cipher().encrypt(secret.encode()).decode()
            db.session.commit()
        return pyotp.TOTP(secret).now()

    try:
        data, registered = account()
        token = registered["access_token"]
        enrollment = request("POST", "/business/api/enable-2fa", 200, token, json=data)
        secret = pyotp.parse_uri(enrollment["otpauth_url"]).secret
        activated = request(
            "POST",
            "/business/api/verify-2fa",
            200,
            token,
            json={**data, "otp": pyotp.TOTP(secret).now()},
        )
        request("GET", "/business/api/me", 401, token)
        request("POST", "/business/api/refresh", 401, registered["refresh_token"])
        request("POST", "/business/api/login", 401, json=data)
        request("POST", "/auth/api/login", 401, json=data)
        completed.append(
            "real enrollment invalidates Flask/Go/Firebase-compatible legacy sessions"
        )
        request(
            "POST",
            "/business/api/mfa/recover",
            401,
            json={**data, "recovery_code": "invalid"},
        )
        request(
            "POST",
            "/business/api/mfa/recover",
            200,
            json={**data, "recovery_code": activated["recovery_codes"][0]},
        )
        request(
            "POST",
            "/business/api/mfa/recover",
            401,
            json={**data, "recovery_code": activated["recovery_codes"][0]},
        )
        recovered = request("POST", "/auth/api/login", 200, json=data)
        request("GET", "/business/api/me", 200, recovered["token"])
        completed.append(
            "offline recovery crosses Flask/Go, consumes codes and permits authenticator replacement"
        )

        data, registered = account("auth")
        otp = seed_mfa(registered["user"]["id"])
        request("POST", "/auth/api/login", 401, json=data)
        login = request("POST", "/auth/api/login", 200, json={**data, "otp": otp})
        request("GET", "/business/api/me", 200, login["token"])
        request("POST", "/auth/api/login", 401, json={**data, "otp": otp})
        renewed = request("POST", "/business/api/refresh", 200, login["refresh_token"])
        request("POST", "/business/api/refresh", 401, login["refresh_token"])
        request("DELETE", "/business/api/logout", 200, renewed["access_token"])
        request("GET", "/business/api/me", 401, renewed["access_token"])
        completed.append(
            "Go delegates OTP issuance; replay/refresh reuse/logout rejected by business"
        )

        data, registered = account("auth")
        otp = seed_mfa(registered["user"]["id"])
        browser = requests.Session()
        browser.trust_env = False
        browser.headers["Host"] = "localhost:38080"
        csrf = browser.get(origin + "/api/auth/csrf", timeout=10).json()["csrfToken"]
        response = browser.post(
            origin + "/api/auth/callback/credentials",
            data={
                **data,
                "otp": otp,
                "csrfToken": csrf,
                "json": "true",
                "callbackUrl": "http://localhost:38080/customer",
            },
            timeout=15,
        )
        assert response.status_code == 200
        session = browser.get(origin + "/api/auth/session", timeout=10).json()
        assert session.get("user", {}).get("id") == registered["user"]["id"], session
        request("GET", "/business/api/me", 200, session["accessToken"])
        completed.append(
            "NextAuth forwards optional OTP through GraphQL and retains SQL identity"
        )

        data, registered = account()
        firebase = http.post(
            "http://firebase:9099/identitytoolkit.googleapis.com/v1/accounts:signUp?key=local",
            json={
                "email": data["email"],
                "password": password,
                "returnSecureToken": True,
            },
            timeout=8,
        ).json()
        firebase_tokens.append(firebase["idToken"])
        body = {"firebase_token": firebase["idToken"]}
        request(
            "POST",
            "/business/api/identity/firebase/link",
            201,
            registered["access_token"],
            json={**body, "password": password},
        )
        prior = request(
            "POST", "/business/api/identity/firebase/session", 200, json=body
        )
        otp = seed_mfa(registered["user"]["id"])
        request("GET", "/business/api/me", 401, prior["access_token"])
        request("POST", "/business/api/identity/firebase/session", 401, json=body)
        session = request(
            "POST",
            "/business/api/identity/firebase/session",
            200,
            json={**body, "otp": otp},
        )
        request("GET", "/business/api/me", 200, session["access_token"])
        request(
            "POST",
            "/business/api/identity/firebase/session",
            401,
            json={**body, "otp": otp},
        )
        completed.append(
            "Firebase proof remains required with SQL MFA; legacy delegated session and OTP reuse rejected"
        )
        request(
            "PUT",
            f"/business/api/user/{registered['user']['id']}",
            200,
            session["access_token"],
            json={
                "email": data["email"],
                "name": data["name"],
                "password": "Changed-synthetic-password-32!",
            },
        )
        request("GET", "/business/api/me", 401, session["access_token"])
        request("POST", "/business/api/identity/firebase/session", 403, json=body)
        completed.append(
            "password policy revokes provider link; an old Firebase proof cannot renew SQL access"
        )
        for kind, samples in timings.items():
            p95 = sorted(samples)[math.ceil(0.95 * len(samples)) - 1]
            assert p95 <= budgets["max_" + kind + "_p95_ms"], (kind, p95)
    finally:
        for token in firebase_tokens:
            response = http.post(
                "http://firebase:9099/identitytoolkit.googleapis.com/v1/accounts:delete?key=local",
                json={"idToken": token},
                timeout=8,
            )
            assert response.status_code == 200
        with app.app_context():
            for user_id in users:
                db.session.execute(
                    text("DELETE FROM session_revocation WHERE subject=:subject"),
                    {"subject": str(user_id)},
                )
                db.session.execute(
                    text("DELETE FROM identity_link WHERE user_id=:id"), {"id": user_id}
                )
                db.session.execute(
                    text("DELETE FROM client WHERE id=:id"), {"id": user_id}
                )
                db.session.execute(
                    text("DELETE FROM userr WHERE id=:id"), {"id": user_id}
                )
            db.session.commit()
    print(
        json.dumps(
            {
                "passed": True,
                "scenarios": completed,
                "cleanup_complete": True,
                "providers_contacted": False,
                "firebase": "local emulator only",
                "latency_samples_ms": timings,
                "unexpected_errors": 0,
                "budgets": budgets,
            }
        )
    )


if __name__ == "__main__":
    main()
