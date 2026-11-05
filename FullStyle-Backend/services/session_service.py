"""Additive refresh and explicit proof-based Firebase linking."""

import hashlib
import hmac
import json
import os
import re
import time
from datetime import timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    decode_token,
    get_jwt,
    jwt_required,
)
from sqlalchemy.exc import IntegrityError

from config.db_config import db
from models.completion_model import RefreshExchange
from models.session_model import IdentityLink, RevokedToken
from models.user_model import UserModel
from utils.account_security import (
    cipher,
    policy,
    session_pair,
    session_valid,
    verify_otp,
)
from utils.authorization import principal_id
from utils.sessions import revoked

sessions = Blueprint("sessions", __name__)


@sessions.post("/api/refresh")
@jwt_required(refresh=True, skip_revocation_check=True)
def refresh():
    principal_id()
    claims = get_jwt()
    policy(int(claims["sub"]), lock=True)
    if not session_valid(claims, int(claims["sub"])):
        db.session.rollback()
        return jsonify(message="Session policy changed"), 401
    key = request.headers.get("Idempotency-Key")
    if key is not None and not re.fullmatch(r"[a-f0-9]{64}", key):
        db.session.rollback()
        return jsonify(message="Invalid idempotency key"), 400
    key_hash = hashlib.sha256(key.encode()).hexdigest() if key else None
    previous = db.session.get(RefreshExchange, claims["jti"])
    if revoked(claims):
        if (
            previous
            and key_hash
            and hmac.compare_digest(previous.key_hash, key_hash)
            and previous.expires_at >= int(time.time())
        ):
            pair = json.loads(cipher().decrypt(previous.encrypted_pair.encode()))
            if not any(revoked(decode_token(value)) for value in pair.values()):
                db.session.rollback()
                return jsonify(**pair)
        db.session.rollback()
        return jsonify(message="Refresh already consumed"), 401
    db.session.add(
        RevokedToken(
            subject=claims["sub"],
            token_type=claims["type"],
            jti=claims["jti"],
            expires_at=claims["exp"],
        )
    )
    tokens = session_pair(
        int(claims["sub"]),
        mfa=claims.get("mfa", False),
        family=claims.get("session_family", claims["jti"]),
    )
    if key_hash:
        # The key is a server-side HMAC in NextAuth, absent from browser sessions.
        # A 15s window lets concurrent replicas return the identical rotated pair.
        RefreshExchange.query.filter(RefreshExchange.expires_at < int(time.time())).delete()
        db.session.add(
            RefreshExchange(
                jti=claims["jti"],
                user_id=int(claims["sub"]),
                key_hash=key_hash,
                encrypted_pair=cipher().encrypt(json.dumps(tokens).encode()).decode(),
                expires_at=int(time.time()) + 15,
            )
        )
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(message="Refresh already consumed"), 401
    return jsonify(**tokens)


def local_firebase_auth():
    if (
        os.getenv("LOCAL_RUNTIME") != "true"
        or os.getenv("FIREBASE_AUTH_EMULATOR_HOST") != "firebase:9099"
    ):
        raise RuntimeError("Firebase linking requires the configured local emulator")
    import firebase_admin
    from firebase_admin import auth

    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(options={"projectId": "demo-fullstyle", "httpTimeout": 5})
    return auth


def firebase_identity(token, require_recent=False):
    auth = local_firebase_auth()
    claims = auth.verify_id_token(token, check_revoked=True)
    if require_recent and time.time() - claims.get("auth_time", 0) > 300:
        raise ValueError("Recent Firebase authentication required")
    return claims


def firebase_session_active(claims, user_id):
    try:
        subject = claims["firebase_uid"]
        link = db.session.get(IdentityLink, ("firebase", subject))
        account = local_firebase_auth().get_user(subject)
        return bool(
            link
            and link.user_id == user_id
            and not account.disabled
            and claims["firebase_auth_time"] * 1000 >= account.tokens_valid_after_timestamp
        )
    except Exception:
        return False


@sessions.post("/api/identity/firebase/link")
@jwt_required()
def link_firebase():
    user = UserModel.find_by_id(principal_id())
    body = request.get_json(silent=True) or {}
    policy(user.id, lock=True)
    db.session.refresh(user)
    if (
        not isinstance(body, dict)
        or not user.active
        or not session_valid(get_jwt(), user.id)
        or not user.check_password(body.get("password", ""))
    ):
        return jsonify(message="Current SQL credentials required"), 401
    try:
        subject = firebase_identity(body.get("firebase_token", ""), require_recent=True)["uid"]
    except RuntimeError:
        return jsonify(message="Firebase adapter unavailable"), 503
    except Exception:
        return jsonify(message="Invalid Firebase identity"), 401
    existing = db.session.get(IdentityLink, ("firebase", subject))
    if existing:
        return (
            (jsonify(linked=True), 200)
            if existing.user_id == user.id
            else (jsonify(message="Identity already linked"), 409)
        )
    db.session.add(IdentityLink(provider="firebase", subject=subject, user_id=user.id))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(message="Identity already linked"), 409
    return jsonify(linked=True), 201


@sessions.post("/api/identity/firebase/session")
def firebase_session():
    body = request.get_json(silent=True) or {}
    try:
        proof = firebase_identity(body.get("firebase_token", ""))
        subject = proof["uid"]
    except RuntimeError:
        return jsonify(message="Firebase adapter unavailable"), 503
    except Exception:
        return jsonify(message="Invalid Firebase identity"), 401
    link = db.session.get(IdentityLink, ("firebase", subject))
    user = UserModel.find_by_id(link.user_id) if link else None
    if not user:
        return jsonify(message="Explicit account linking required"), 403
    state = policy(user.id, lock=True)
    db.session.refresh(user)
    link = db.session.get(IdentityLink, ("firebase", subject), populate_existing=True)
    if not user.active or link is None or link.user_id != user.id:
        db.session.rollback()
        return jsonify(message="Explicit account linking required"), 403
    if state.enabled and not verify_otp(state, body.get("otp", "")):
        db.session.commit()
        return jsonify(message="MFA required", mfa_required=True), 401
    extra = {"session_epoch": state.epoch, "mfa": state.enabled}
    db.session.commit()
    return jsonify(
        user=user.json(),
        access_token=create_access_token(
            identity=str(user.id),
            additional_claims={
                **extra,
                "identity_provider": "firebase",
                "firebase_uid": subject,
                "firebase_auth_time": proof["auth_time"],
            },
            expires_delta=timedelta(seconds=min(900, proof["exp"] - int(time.time()))),
        ),
        # Renewal always requires a fresh, non-revoked Firebase proof.
        renewal="firebase-proof",
    )
