"""Shared access/refresh validation with durable, subject-scoped revocation."""

from flask import jsonify
from flask_jwt_extended import JWTManager
from sqlalchemy import and_, or_

from models.session_model import RevokedToken
from models.user_model import UserModel
from utils.account_security import session_valid


def revoked(claims):
    return (
        RevokedToken.query.filter(
            RevokedToken.subject == claims.get("sub"),
            or_(
                and_(
                    RevokedToken.token_type == claims.get("type"),
                    RevokedToken.jti == claims.get("jti"),
                ),
                and_(
                    RevokedToken.token_type == "family",
                    RevokedToken.jti == claims.get("session_family", claims.get("jti")),
                ),
            ),
        ).first()
        is not None
    )


def configure_sessions(app):
    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader
    def check_revocation(_header, claims):
        return revoked(claims)

    @jwt.token_verification_loader
    def active_identity(_header, claims):
        subject = claims.get("sub")
        if claims.get("identity_provider") == "firebase":
            from services.session_service import firebase_session_active

            if (
                not isinstance(subject, str)
                or not subject.isdecimal()
                or not firebase_session_active(claims, int(subject))
            ):
                return False
        return (
            isinstance(subject, str)
            and subject.isdecimal()
            and UserModel.find_by_id(int(subject)) is not None
            and session_valid(claims, int(subject))
            and not claims.get("purpose")
            and claims.get("type") in ("access", "refresh")
            and isinstance(claims.get("jti"), str)
        )

    @jwt.token_verification_failed_loader
    def invalid_identity(_header, _claims):
        return jsonify(message="Invalid or inactive identity"), 401

    return jwt
