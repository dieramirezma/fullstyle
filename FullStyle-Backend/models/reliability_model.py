"""Additive durable mail intents, synthetic delivery receipts and shared chat turns."""

from config.db_config import db


class MailEvent(db.Model):
    __tablename__ = "mail_event"
    id = db.Column(db.String(64), primary_key=True)
    payload = db.Column(db.JSON, nullable=False)
    payload_hash = db.Column(db.String(64), nullable=False)
    state = db.Column(db.String(20), nullable=False, server_default="pending", index=True)
    attempts = db.Column(db.Integer, nullable=False, server_default="0")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    next_attempt = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=db.func.now(), index=True
    )
    delivered_at = db.Column(db.DateTime(timezone=True))
    last_error = db.Column(db.String(80))


class MailDelivery(db.Model):
    __tablename__ = "mail_delivery"
    event_id = db.Column(
        db.String(64), db.ForeignKey("mail_event.id", ondelete="CASCADE"), primary_key=True
    )
    ordinal = db.Column(db.Integer, primary_key=True)
    result = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())


class ChatTurn(db.Model):
    __tablename__ = "chat_turn"
    sequence = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("userr.id", ondelete="CASCADE"), nullable=False)
    session_id = db.Column(db.String(120), nullable=False)
    operation_id = db.Column(db.String(80), nullable=False)
    message = db.Column(db.Text, nullable=False)
    message_hash = db.Column(db.String(64), nullable=False)
    reply = db.Column(db.Text)
    state = db.Column(db.String(20), nullable=False, server_default="pending")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    reviewed_at = db.Column(db.DateTime(timezone=True))
    review_note = db.Column(db.String(500))
    content_expires_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.text("now() + interval '30 days'"),
    )
    __table_args__ = (
        db.UniqueConstraint("user_id", "session_id", "operation_id"),
        db.Index("ix_chat_history", "user_id", "session_id", "sequence"),
    )
