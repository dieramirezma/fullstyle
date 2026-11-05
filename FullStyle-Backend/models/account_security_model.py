"""Optional MFA policy and an epoch shared by all session issuers."""

from config.db_config import db


class AccountSecurity(db.Model):
    __tablename__ = "account_security"
    user_id = db.Column(db.Integer, db.ForeignKey("userr.id", ondelete="CASCADE"), primary_key=True)
    epoch = db.Column(db.Integer, nullable=False, default=0)
    enabled = db.Column(db.Boolean, nullable=False, default=False)
    secret = db.Column(db.Text)
    pending_until = db.Column(db.BigInteger, nullable=False, default=0)
    last_step = db.Column(db.BigInteger, nullable=False, default=-1)
    failures = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.BigInteger, nullable=False, default=0)
