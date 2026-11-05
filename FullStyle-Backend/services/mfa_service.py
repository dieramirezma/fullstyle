"""Compatible enrollment routes; current password and verified identity required."""

import time

import pyotp
from flask import request
from flask_jwt_extended import get_jwt, jwt_required
from flask_restful import Resource

from config.db_config import db
from models.completion_model import RecoveryCode
from models.user_model import UserModel
from utils.account_security import bump_epoch, cipher, policy, session_valid, verify_otp
from utils.authorization import principal_id
from utils.mfa_recovery import issue_codes


def actor_and_body():
    actor = UserModel.find_by_id(principal_id())
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not isinstance(body.get("email"), str):
        return None, {}, ({"message": "JSON object and email required"}, 400)
    if body["email"].lower() != actor.email.lower():
        return None, body, ({"message": "Forbidden"}, 403)
    if not actor.check_password(body.get("password", "")):
        return None, body, ({"message": "Current password required"}, 401)
    return actor, body, None


def current_under_lock(actor, body):
    db.session.refresh(actor)
    if (
        not actor.active
        or not actor.check_password(body.get("password", ""))
        or not session_valid(get_jwt(), actor.id)
    ):
        db.session.rollback()
        return False
    return True


class Enable2FA(Resource):
    @jwt_required()
    def post(self):
        actor, body, error = actor_and_body()
        if error:
            return error
        state = policy(actor.id, lock=True)
        if not current_under_lock(actor, body):
            return {"message": "Current session and password required"}, 401
        if state.enabled:
            db.session.rollback()
            return {"message": "MFA already enabled"}, 409
        now = int(time.time())
        # Repeated page requests reuse the pending secret; they cannot reset failures.
        if not state.secret or state.pending_until < now:
            secret = pyotp.random_base32()
            state.secret = cipher().encrypt(secret.encode()).decode()
            state.pending_until = now + 600
        secret = cipher().decrypt(state.secret.encode()).decode()
        db.session.commit()
        return {
            "otpauth_url": pyotp.TOTP(secret).provisioning_uri(actor.email, issuer_name="FullStyle")
        }, 200

    @jwt_required()
    def delete(self):
        actor, body, error = actor_and_body()
        if error:
            return error
        state = policy(actor.id, lock=True)
        if not current_under_lock(actor, body):
            return {"message": "Current session and password required"}, 401
        if not state.enabled or not verify_otp(state, body.get("otp", "")):
            db.session.commit()
            return {"message": "Invalid or replayed OTP"}, 401
        state.enabled = False
        state.secret = None
        RecoveryCode.query.filter_by(user_id=actor.id).delete()
        bump_epoch(state)
        db.session.commit()
        return {"message": "MFA disabled; sign in again"}, 200


class Verify2FA(Resource):
    @jwt_required()
    def post(self):
        actor, body, error = actor_and_body()
        if error:
            return error
        state = policy(actor.id, lock=True)
        if not current_under_lock(actor, body):
            return {"message": "Current session and password required"}, 401
        if state.enabled or state.pending_until < int(time.time()):
            db.session.rollback()
            return {"message": "Enrollment expired or already completed"}, 409
        if not verify_otp(state, body.get("otp", "")):
            db.session.commit()
            return {"message": "Invalid or replayed OTP"}, 401
        state.enabled = True
        state.pending_until = 0
        bump_epoch(state)
        codes = issue_codes(actor.id)
        db.session.commit()
        return {
            "message": "MFA enabled; save recovery codes and sign in again",
            "recovery_codes": codes,
        }, 200
