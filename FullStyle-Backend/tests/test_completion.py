"""Regressions for offline recovery and cross-replica single-use refresh races."""

import time
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pyotp
import pytest
from flask_jwt_extended import decode_token

from config.db_config import db
from models.account_security_model import AccountSecurity
from models.completion_model import RecoveryCode, RefreshExchange
from models.session_model import IdentityLink
from models.user_model import UserModel


def headers(token, key=None):
    return {"Authorization": "Bearer " + token, **({"Idempotency-Key": key} if key else {})}


def activate(client, token, data):
    response = client.post("/api/enable-2fa", json=data, headers=headers(token))
    secret = parse_qs(urlparse(response.json["otpauth_url"]).query)["secret"][0]
    response = client.post(
        "/api/verify-2fa", json={**data, "otp": pyotp.TOTP(secret).now()}, headers=headers(token)
    )
    assert response.status_code == 200, response.json
    return response.json["recovery_codes"], secret


def test_recovery_requires_password_consumes_all_codes_and_revokes_sessions(
    client, app, token, setup_user
):
    codes, secret = activate(client, token, setup_user)
    assert len(codes) == len(set(codes)) == 10
    with app.app_context():
        assert RecoveryCode.query.count() == 10
        assert all(c not in {r.digest for r in RecoveryCode.query.all()} for c in codes)
        db.session.add(
            IdentityLink(
                provider="firebase",
                subject="synthetic-recovery-proof",
                user_id=AccountSecurity.query.one().user_id,
            )
        )
        db.session.commit()
    body = {**setup_user, "recovery_code": codes[0]}
    assert client.post("/api/mfa/recover", json={**body, "password": "wrong"}).status_code == 401
    later = int(time.time()) + 60
    with patch("utils.account_security.time.time", return_value=later):
        signed = client.post(
            "/api/login", json={**setup_user, "otp": pyotp.TOTP(secret).at(later)}
        ).json
    assert client.post("/api/mfa/recover", json=body).status_code == 200
    assert client.get("/api/me", headers=headers(signed["access_token"])).status_code == 401
    assert client.post("/api/refresh", headers=headers(signed["refresh_token"])).status_code == 401
    assert client.post("/api/mfa/recover", json=body).status_code == 401
    assert client.post("/api/login", json=setup_user).status_code == 200
    with app.app_context():
        state = AccountSecurity.query.one()
        assert not state.enabled and state.secret is None and state.epoch == 2
        assert RecoveryCode.query.count() == 0
        assert IdentityLink.query.count() == 0


def test_recovery_lockout_persists(client, app, token, setup_user):
    codes, _ = activate(client, token, setup_user)
    for _ in range(5):
        assert (
            client.post("/api/mfa/recover", json={**setup_user, "recovery_code": "bad"}).status_code
            == 401
        )
    assert (
        client.post("/api/mfa/recover", json={**setup_user, "recovery_code": codes[0]}).status_code
        == 401
    )
    with app.app_context():
        assert AccountSecurity.query.one().locked_until > time.time()
        assert RecoveryCode.query.count() == 10


@pytest.mark.parametrize("submitted_email", ["MiXeD@synthetic.invalid", "mixed@synthetic.invalid"])
def test_recovery_preserves_legacy_email_case_and_password_hash(
    client, app, token, setup_user, submitted_email
):
    with app.app_context():
        account = UserModel.query.one()
        account.email = "MiXeD@synthetic.invalid"
        original_hash = account.password
        db.session.commit()
    data = {**setup_user, "email": "MiXeD@synthetic.invalid"}
    codes, _ = activate(client, token, data)
    assert (
        client.post(
            "/api/mfa/recover", json={**data, "email": submitted_email, "recovery_code": codes[0]}
        ).status_code
        == 200
    )
    with app.app_context():
        assert UserModel.query.one().password == original_hash


def test_two_simultaneous_recoveries_only_one_succeeds(client, app, token, setup_user):
    codes, _ = activate(client, token, setup_user)
    barrier = Barrier(2)

    def recover(_):
        with app.test_client() as peer:
            barrier.wait(timeout=10)
            return peer.post(
                "/api/mfa/recover", json={**setup_user, "recovery_code": codes[0]}
            ).status_code

    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(recover, range(2))) == [200, 401]


def test_simultaneous_refresh_returns_same_pair_only_for_same_key(client, app, setup_user):
    old = client.post("/api/login", json=setup_user).json["refresh_token"]
    key = "a" * 64
    barrier = Barrier(2)

    def renew(_):
        with app.test_client() as peer:
            barrier.wait(timeout=10)
            response = peer.post("/api/refresh", headers=headers(old, key))
            assert response.status_code == 200, response.json
            return response.json

    with ThreadPoolExecutor(2) as pool:
        pairs = list(pool.map(renew, range(2)))
    assert pairs[0] == pairs[1]
    assert client.post("/api/refresh", headers=headers(old)).status_code == 401
    assert client.post("/api/refresh", headers=headers(old, "b" * 64)).status_code == 401
    with app.app_context():
        row = RefreshExchange.query.one()
        assert pairs[0]["refresh_token"] not in row.encrypted_pair
        assert decode_token(pairs[0]["refresh_token"])["type"] == "refresh"
    # Logout the winning refresh; a delayed tab must not recover it from the cache.
    assert (
        client.delete("/api/logout", headers=headers(pairs[0]["refresh_token"])).status_code == 200
    )
    assert client.post("/api/refresh", headers=headers(old, key)).status_code == 401


def test_refresh_retry_window_expires(client, app, setup_user):
    old = client.post("/api/login", json=setup_user).json["refresh_token"]
    assert client.post("/api/refresh", headers=headers(old, "a" * 64)).status_code == 200
    with app.app_context():
        RefreshExchange.query.one().expires_at = 1
        db.session.commit()
    assert client.post("/api/refresh", headers=headers(old, "a" * 64)).status_code == 401


def test_stale_tab_logout_revokes_rotated_descendants_but_not_another_login(client, setup_user):
    first = client.post("/api/login", json=setup_user).json
    other = client.post("/api/login", json=setup_user).json
    pair = client.post("/api/refresh", headers=headers(first["refresh_token"], "a" * 64)).json
    assert client.delete("/api/logout", headers=headers(first["refresh_token"])).status_code == 200
    assert client.get("/api/me", headers=headers(pair["access_token"])).status_code == 401
    assert client.post("/api/refresh", headers=headers(pair["refresh_token"])).status_code == 401
    assert (
        client.post("/api/refresh", headers=headers(first["refresh_token"], "a" * 64)).status_code
        == 401
    )
    assert client.get("/api/me", headers=headers(other["access_token"])).status_code == 200
