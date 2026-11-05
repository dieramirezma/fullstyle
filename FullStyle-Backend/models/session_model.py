"""Additive session and identity tables; no changes to legacy password columns."""

from config.db_config import db


class RevokedToken(db.Model):
    __tablename__ = "session_revocation"
    subject = db.Column(db.String(100), primary_key=True)
    token_type = db.Column(db.String(20), primary_key=True)
    jti = db.Column(db.String(100), primary_key=True)
    expires_at = db.Column(db.BigInteger, nullable=False)


class IdentityLink(db.Model):
    __tablename__ = "identity_link"
    provider = db.Column(db.String(30), primary_key=True)
    subject = db.Column(db.String(150), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("userr.id"), nullable=False)
    __table_args__ = (db.UniqueConstraint("provider", "user_id"),)


class ProviderReceipt(db.Model):
    __tablename__ = "provider_receipt"
    id = db.Column(db.String(36), primary_key=True)
    provider = db.Column(db.String(30), nullable=False)
    transaction_id = db.Column(db.String(150), nullable=False)
    payload = db.Column(db.JSON, nullable=False)
    state = db.Column(db.String(30), nullable=False, default="received")
