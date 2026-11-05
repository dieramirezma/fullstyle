"""MFA/session tests assert HTTP rejection and durable policy, never only mocks."""

import time
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pyotp
import pytest
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token
from sqlalchemy import text

from config.db_config import db
from models.account_security_model import AccountSecurity
from models.user_model import UserModel
from utils.account_security import cipher


def headers(token):
    return {"Authorization": "Bearer " + token}


def enroll(client, token, data):
    result = client.post("/api/enable-2fa", headers=headers(token), json=data)
    assert result.status_code == 200, result.json
    return parse_qs(urlparse(result.json["otpauth_url"]).query)["secret"][0]


def activate(client, token, data, secret):
    result = client.post(
        "/api/verify-2fa", headers=headers(token), json={**data, "otp": pyotp.TOTP(secret).now()}
    )
    assert result.status_code == 200, result.json


def test_enrollment_requires_owner_password_and_confirmation(client, app, token, setup_user):
    assert client.post("/api/enable-2fa", json=setup_user).status_code == 401
    assert (
        client.post(
            "/api/enable-2fa",
            headers=headers(token),
            json={**setup_user, "email": "foreign@synthetic.invalid"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/enable-2fa", headers=headers(token), json={**setup_user, "password": "wrong"}
        ).status_code
        == 401
    )
    secret = enroll(client, token, setup_user)
    assert secret == enroll(client, token, setup_user)
    with app.app_context():
        state = AccountSecurity.query.one()
        assert not state.enabled and state.epoch == 0
        assert state.secret != secret and secret not in state.secret
        assert cipher().decrypt(state.secret.encode()).decode() == secret
    assert client.get("/api/me", headers=headers(token)).status_code == 200


def test_mfa_activation_revokes_legacy_tokens_and_otp_replay(client, app, token, setup_user):
    prior = client.post("/api/login", json=setup_user).json
    secret = enroll(client, token, setup_user)
    activate(client, token, setup_user, secret)
    assert client.get("/api/me", headers=headers(token)).status_code == 401
    assert client.post("/api/refresh", headers=headers(prior["refresh_token"])).status_code == 401
    # The enrollment OTP is already consumed; knowing the password is insufficient.
    assert client.post("/api/login", json=setup_user).status_code == 401
    assert (
        client.post("/api/login", json={**setup_user, "otp": pyotp.TOTP(secret).now()}).status_code
        == 401
    )
    later = int(time.time()) + 60
    with patch("utils.account_security.time.time", return_value=later):
        result = client.post("/api/login", json={**setup_user, "otp": pyotp.TOTP(secret).at(later)})
        assert result.status_code == 200, result.json
        new = result.json
        assert (
            client.post(
                "/api/login", json={**setup_user, "otp": pyotp.TOTP(secret).at(later)}
            ).status_code
            == 401
        )
    assert client.get("/api/me", headers=headers(new["access_token"])).status_code == 200
    renewed = client.post("/api/refresh", headers=headers(new["refresh_token"]))
    assert renewed.status_code == 200, renewed.json
    assert client.post("/api/refresh", headers=headers(new["refresh_token"])).status_code == 401
    with app.app_context():
        claims = decode_token(renewed.json["access_token"])
        assert claims["mfa"] is True and claims["session_epoch"] == 1
    assert client.get("/api/me", headers=headers(renewed.json["access_token"])).status_code == 200


def test_enrollment_expiry_and_failed_attempt_lockout(client, app, token, setup_user):
    secret = enroll(client, token, setup_user)
    with app.app_context():
        AccountSecurity.query.one().pending_until = 1
        db.session.commit()
    assert (
        client.post(
            "/api/verify-2fa",
            headers=headers(token),
            json={**setup_user, "otp": pyotp.TOTP(secret).now()},
        ).status_code
        == 409
    )
    secret = enroll(client, token, setup_user)
    activate(client, token, setup_user, secret)
    for _ in range(5):
        assert client.post("/api/login", json={**setup_user, "otp": "bad"}).status_code == 401
    later = int(time.time()) + 60
    with patch("utils.account_security.time.time", return_value=later):
        assert (
            client.post(
                "/api/login", json={**setup_user, "otp": pyotp.TOTP(secret).at(later)}
            ).status_code
            == 401
        )
    with app.app_context():
        assert AccountSecurity.query.one().locked_until > later


def test_legacy_hash_and_sessions_survive_until_policy_changes(client, app, legacy_user):
    data = {"email": "legacy@synthetic.invalid", "password": "Password123"}
    with app.app_context():
        before = db.session.get(UserModel, legacy_user).password
        legacy = create_access_token(identity=str(legacy_user))
    assert client.get("/api/me", headers=headers(legacy)).status_code == 200
    login = client.post("/api/login", json=data)
    assert login.status_code == 200
    with app.app_context():
        assert db.session.get(UserModel, legacy_user).password == before
    updated = client.put(
        f"/api/user/{legacy_user}",
        headers=headers(login.json["access_token"]),
        json={"email": data["email"], "name": "legacy", "password": "Changed123"},
    )
    assert updated.status_code == 200, updated.json
    assert client.get("/api/me", headers=headers(legacy)).status_code == 401
    assert (
        client.post("/api/refresh", headers=headers(login.json["refresh_token"])).status_code == 401
    )
    assert client.post("/api/login", json=data).status_code == 401
    assert client.post("/api/login", json={**data, "password": "Changed123"}).status_code == 200


@pytest.mark.parametrize("kind", ["access", "refresh"])
def test_epoch_cannot_be_bypassed_with_other_issuer_claims(client, app, token, setup_user, kind):
    secret = enroll(client, token, setup_user)
    activate(client, token, setup_user, secret)
    with app.app_context():
        user = UserModel.query.one()
        issuer = create_access_token if kind == "access" else create_refresh_token
        forged_policy = issuer(
            identity=str(user.id),
            additional_claims={
                "session_epoch": 1,
                "identity_provider": "go",
                "mfa": False,
            },
        )
    response = (
        client.get("/api/me", headers=headers(forged_policy))
        if kind == "access"
        else client.post("/api/refresh", headers=headers(forged_policy))
    )
    assert response.status_code == 401


def test_harness_uses_private_schema(app):
    with app.app_context():
        assert (
            db.session.execute(text("SELECT current_schema()")).scalar_one()
            == app.config["TEST_SCHEMA"]
        )
        assert db.session.execute(text("SELECT count(*) FROM schema_migration")).scalar_one() >= 2


def test_soft_deleted_account_cannot_revive_legacy_sessions(client, app, token, setup_user):
    before = client.post("/api/login", json=setup_user).json
    user_id = before["user"]["id"]
    assert client.delete(f"/api/user/{user_id}", headers=headers(token)).status_code == 200
    assert client.get("/api/me", headers=headers(token)).status_code == 401
    assert (
        client.post("/api/register", json={**setup_user, "password": "Wrong123"}).status_code == 401
    )
    assert client.post("/api/register", json=setup_user).status_code == 201
    assert client.get("/api/me", headers=headers(token)).status_code == 401
    assert client.post("/api/refresh", headers=headers(before["refresh_token"])).status_code == 401
    login = client.post("/api/login", json=setup_user)
    assert login.status_code == 200
    assert client.get("/api/me", headers=headers(login.json["access_token"])).status_code == 200


def test_disable_requires_fresh_otp_and_revokes_mfa_sessions(client, app, token, setup_user):
    secret = enroll(client, token, setup_user)
    activate(client, token, setup_user, secret)
    later = int(time.time()) + 60
    with patch("utils.account_security.time.time", return_value=later):
        login = client.post("/api/login", json={**setup_user, "otp": pyotp.TOTP(secret).at(later)})
        assert login.status_code == 200
        assert (
            client.delete(
                "/api/enable-2fa",
                headers=headers(login.json["access_token"]),
                json={**setup_user, "otp": pyotp.TOTP(secret).at(later)},
            ).status_code
            == 401
        )
    later += 60
    with patch("utils.account_security.time.time", return_value=later):
        result = client.delete(
            "/api/enable-2fa",
            headers=headers(login.json["access_token"]),
            json={**setup_user, "otp": pyotp.TOTP(secret).at(later)},
        )
        assert result.status_code == 200, result.json
    assert client.get("/api/me", headers=headers(login.json["access_token"])).status_code == 401
    assert (
        client.post("/api/refresh", headers=headers(login.json["refresh_token"])).status_code == 401
    )
    assert client.post("/api/login", json=setup_user).status_code == 200
    with app.app_context():
        state = AccountSecurity.query.one()
        assert state.secret is None and not state.enabled and state.epoch == 2
