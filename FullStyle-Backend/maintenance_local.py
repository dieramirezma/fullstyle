"""Bounded local housekeeping; locking keeps API writes and replica jobs consistent."""

import re
from datetime import datetime, timezone

from sqlalchemy import text

from config.db_config import db
from models.appointment_model import AppointmentModel
from models.consistency_model import PaymentIntent
from services.local_finance import close_intent, local_only


def maintain():
    local_only()
    schema = db.session.execute(text("SELECT current_schema()")).scalar_one()
    if schema != "public" and not re.fullmatch(r"phase6_[a-f0-9]{32}", schema):
        raise ValueError("Unexpected maintenance schema")
    if not db.session.execute(
        text("SELECT pg_try_advisory_xact_lock(hashtextextended(:key,0))"),
        {"key": schema + ":local-maintenance"},
    ).scalar_one():
        db.session.rollback()
        return 0
    # Read candidates without locking intent rows before appointments: event writes
    # lock appointments first. Recheck after taking each booking lock.
    candidates = db.session.execute(
        text(
            "SELECT reference,appointment_id FROM payment_intent WHERE state='open' AND expires_at<=now() ORDER BY appointment_id LIMIT 100"
        )
    ).all()
    expired = 0
    for reference, appointment_id in candidates:
        appointment = (
            AppointmentModel.query.filter_by(id=appointment_id)
            .populate_existing()
            .with_for_update(skip_locked=True)
            .first()
        )
        if appointment is None:
            continue
        intent = db.session.get(PaymentIntent, reference, populate_existing=True)
        if intent.state == "open" and intent.expires_at <= datetime.now(timezone.utc):
            close_intent(intent, appointment, "expired")
            expired += 1
    db.session.execute(
        text("DELETE FROM refresh_exchange WHERE expires_at < extract(epoch FROM now())")
    )
    db.session.execute(
        text(
            "UPDATE manager SET subscriptionactive=false WHERE subscriptionactive=true AND subscriptionfinishdate<=now()"
        )
    )
    db.session.execute(
        text(
            "UPDATE local_subscription SET state='expired' WHERE state='active' AND expires_at<=now()"
        )
    )
    db.session.commit()
    return expired


if __name__ == "__main__":
    from config.server_config import create_app

    with create_app().app_context():
        print(f"PASS: {maintain()} expired bookings closed")
