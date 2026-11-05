"""One transaction owns validation, worker locks and persistence for every write."""

from functools import wraps

from flask_restful import abort
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from config.db_config import db
from models.appointment_model import AppointmentModel
from models.consistency_model import BookingTerms
from models.detail_model import DetailModel
from models.worker_model import WorkerModel
from utils.authorization import authorized_appointment


def transactional(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        try:
            db.session.execute(text("SET LOCAL lock_timeout = '5s'"))
            db.session.execute(text("SET LOCAL statement_timeout = '15s'"))
            result = func(*args, **kwargs)
            status = result[1] if isinstance(result, tuple) else 200
            if 200 <= status < 300:
                db.session.commit()
            else:
                db.session.rollback()
            return result
        except SQLAlchemyError as exc:
            db.session.rollback()
            conflict = getattr(getattr(exc, "orig", None), "pgcode", None) in {
                "55P03",
                "40P01",
                "40001",
                "23505",
            }
            return {
                "message": "Concurrent operation conflict" if conflict else "Database unavailable"
            }, (409 if conflict else 503)
        except Exception:
            db.session.rollback()
            raise

    return wrapped


def lock_appointment(appointment_id):
    # Refresh after waiting: authorization and state must refer to the locked version.
    appointment = (
        AppointmentModel.query.filter_by(id=appointment_id)
        .populate_existing()
        .with_for_update()
        .first()
    )
    if appointment is None:
        abort(404, message="Appointment not found")
    authorized_appointment(appointment_id)
    return appointment


def lock_workers(*worker_ids):
    # Stable order allows moves between workers without inversions.
    for worker_id in sorted(set(worker_ids)):
        if (
            not WorkerModel.query.filter_by(id=worker_id)
            .populate_existing()
            .with_for_update()
            .first()
        ):
            abort(400, message="Worker not found")


def snapshot_terms(appointment):
    terms = db.session.get(BookingTerms, appointment.id)
    if terms is None:
        detail = DetailModel.query.filter_by(
            site_id=appointment.site_id, service_id=appointment.service_id, active=True
        ).first()
        if detail is None or detail.duration <= 0 or detail.price < 0:
            abort(400, message="Invalid service terms")
        terms = BookingTerms(
            appointment_id=appointment.id,
            duration=detail.duration,
            amount=detail.price,
            currency="COP",
        )
        db.session.add(terms)
    return terms


def lock_service_terms(site_id, service_id):
    detail = (
        DetailModel.query.filter_by(site_id=site_id, service_id=service_id, active=True)
        .populate_existing()
        .with_for_update(read=True)
        .first()
    )
    if detail is None:
        abort(400, message="Active service terms required")
    return detail
