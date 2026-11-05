"""Additive booking snapshots, transactional cache epochs and provider ledger."""

from config.db_config import db


class BookingTerms(db.Model):
    __tablename__ = "booking_terms"
    appointment_id = db.Column(
        db.Integer, db.ForeignKey("appointment.id", ondelete="CASCADE"), primary_key=True
    )
    duration = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # whole COP, legacy API unit
    currency = db.Column(db.String(3), nullable=False, default="COP")
    __table_args__ = (
        db.CheckConstraint("duration > 0 AND amount >= 0", name="valid_booking_terms"),
    )


class CacheEpoch(db.Model):
    __tablename__ = "cache_epoch"
    namespace = db.Column(db.String(40), primary_key=True)
    generation = db.Column(db.String(32), nullable=False)


class PaymentIntent(db.Model):
    __tablename__ = "payment_intent"
    reference = db.Column(db.String(36), primary_key=True)
    appointment_id = db.Column(
        db.Integer, db.ForeignKey("appointment.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    payment_id = db.Column(
        db.Integer, db.ForeignKey("payment.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    amount_in_cents = db.Column(db.BigInteger, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="COP")
    __table_args__ = (db.CheckConstraint("amount_in_cents > 0", name="positive_payment_intent"),)
    state = db.Column(db.String(24), nullable=False, server_default="open")
    expires_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.text("now() + interval '15 minutes'"),
    )


class ProviderTransaction(db.Model):
    __tablename__ = "provider_transaction"
    provider = db.Column(db.String(30), primary_key=True)
    transaction_id = db.Column(db.String(150), primary_key=True)
    receipt_id = db.Column(
        db.String(36),
        db.ForeignKey("provider_receipt.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    reference = db.Column(db.String(150))
    amount_in_cents = db.Column(db.BigInteger)
    currency = db.Column(db.String(3))
    status = db.Column(db.String(30), nullable=False)
    verified_payload = db.Column(db.JSON, nullable=False)
    applied_payment_id = db.Column(db.Integer, db.ForeignKey("payment.id"), unique=True)
    resolution = db.Column(db.String(24), nullable=False, server_default="none")
