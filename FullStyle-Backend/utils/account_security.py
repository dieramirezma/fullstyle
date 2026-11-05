"""SQL account policy: encrypted TOTP, bounded attempts, replay and session epochs."""

import time
from datetime import timedelta
from uuid import uuid4

import pyotp
from cryptography.fernet import InvalidToken
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token
from sqlalchemy.dialects.postgresql import insert

from config.db_config import db
from models.account_security_model import AccountSecurity
from models.session_model import IdentityLink
from utils.keyring import load_cipher


def cipher():
    return load_cipher(current_app.config["SECRET_KEY"], current_app.config.get("MFA_KEYRING_FILE"))


def policy(user_id, lock=False):
    if lock:
        db.session.execute(
            insert(AccountSecurity)
            .values(user_id=user_id)
            .on_conflict_do_nothing(index_elements=[AccountSecurity.user_id])
        )
        return (
            AccountSecurity.query.filter_by(user_id=user_id)
            .populate_existing()
            .with_for_update()
            .one()
        )
    return db.session.get(AccountSecurity, user_id)


def session_valid(claims, user_id):
    state = policy(user_id)
    epoch = state.epoch if state else 0
    return claims.get("session_epoch", 0) == epoch and (
        not state or not state.enabled or claims.get("mfa") is True
    )


def session_pair(user_id, mfa=False, family=None):
    state = policy(user_id)
    claims = {
        "session_epoch": state.epoch if state else 0,
        "mfa": mfa,
        "session_family": family or uuid4().hex,
    }
    return {
        "access_token": create_access_token(
            identity=str(user_id), additional_claims=claims, expires_delta=timedelta(hours=1)
        ),
        "refresh_token": create_refresh_token(identity=str(user_id), additional_claims=claims),
    }


def verify_otp(state, otp):
    now = int(time.time())
    if state.locked_until > now:
        return False
    step = now // 30
    try:
        totp = pyotp.TOTP(cipher().decrypt(state.secret.encode()).decode())
        matched = next(
            (
                s
                for s in (step, step - 1)
                if s > state.last_step and totp.verify(str(otp), for_time=s * 30)
            ),
            None,
        )
    except (ValueError, TypeError, InvalidToken):
        matched = None
    if matched is None:
        state.failures += 1
        if state.failures >= 5:
            state.locked_until = now + 300
            state.failures = 0
        return False
    state.last_step = matched
    state.failures = 0
    state.locked_until = 0
    return True


def password_login(user, otp, password):
    state = policy(user.id, lock=True)
    # Re-read under the policy lock after any concurrent password reset commits.
    db.session.refresh(user)
    if not user.active or not user.check_password(password):
        db.session.rollback()
        return None
    if state.enabled and not verify_otp(state, otp):
        db.session.commit()
        return None
    tokens = session_pair(user.id, mfa=state.enabled)
    db.session.commit()
    return tokens


def invalidate_sessions(user_id):
    state = policy(user_id, lock=True)
    bump_epoch(state)


def bump_epoch(state):
    # A previously issued provider proof must not mint a new SQL session after
    # recovery/password/MFA changes. Linking again requires both current proofs.
    state.epoch += 1
    IdentityLink.query.filter_by(user_id=state.user_id).delete()
