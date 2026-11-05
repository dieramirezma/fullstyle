"""Additive recovery, coordinated refresh and auditable local financial workflows."""

from config.db_config import db


class RecoveryCode(db.Model):
    __tablename__ = "mfa_recovery_code"
    user_id = db.Column(db.Integer, db.ForeignKey("userr.id", ondelete="CASCADE"), primary_key=True)
    digest = db.Column(db.String(64), primary_key=True)


class RefreshExchange(db.Model):
    __tablename__ = "refresh_exchange"
    jti = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("userr.id", ondelete="CASCADE"), nullable=False)
    key_hash = db.Column(db.String(64), nullable=False)
    encrypted_pair = db.Column(db.Text, nullable=False)
    expires_at = db.Column(db.BigInteger, nullable=False)


class PaymentAction(db.Model):
    __tablename__ = "payment_action"
    operation_id = db.Column(db.String(80), primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey("payment.id"), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey("userr.id"), nullable=False)
    action = db.Column(db.String(24), nullable=False)
    reason = db.Column(db.String(500), nullable=False)
    transaction_id = db.Column(db.String(150))
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)


class LocalSubscription(db.Model):
    __tablename__ = "local_subscription"
    reference = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("userr.id", ondelete="CASCADE"), nullable=False)
    plan = db.Column(db.String(40), nullable=False)
    amount_in_cents = db.Column(db.BigInteger, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="COP")
    state = db.Column(db.String(24), nullable=False, default="pending")
    expires_at = db.Column(db.DateTime(timezone=True))
    provider_transaction_id = db.Column(db.String(150), unique=True)


class MailReview(db.Model):
    __tablename__ = "mail_review"
    operation_id = db.Column(db.String(80), primary_key=True)
    event_id = db.Column(
        db.String(64), db.ForeignKey("mail_event.id", ondelete="CASCADE"), nullable=False
    )
    actor_id = db.Column(db.Integer, db.ForeignKey("userr.id"), nullable=False)
    reason = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
