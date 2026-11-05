"""Resource policy shared by REST and delegated chatbot requests.

JWT signature/type/expiry are verified by jwt_required before these adapters run.
Roles and ownership come from the database, never request bodies or JWT role hints.
"""

from functools import wraps

from flask import request
from flask_jwt_extended import get_jwt_identity
from flask_restful import abort
from sqlalchemy import or_, select

from models.appointment_model import AppointmentModel
from models.manager_model import ManagerModel
from models.site_model import SiteModel
from models.user_model import UserModel
from models.worker_model import WorkerModel


def principal_id():
    subject = get_jwt_identity()
    if not isinstance(subject, str) or not subject.isdecimal() or int(subject) <= 0:
        abort(401, message="Invalid identity")
    user = UserModel.find_by_id(int(subject))
    if user is None:
        abort(401, message="Inactive or unknown identity")
    return user.id


def require_self(user_id):
    if principal_id() != user_id:
        abort(403, message="Forbidden")


def owned_sites():
    return (
        select(SiteModel.id)
        .join(ManagerModel, SiteModel.manager_id == ManagerModel.id)
        .where(ManagerModel.id == principal_id())
    )


def scoped_appointments(query):
    return query.filter(
        or_(
            AppointmentModel.client_id == principal_id(),
            AppointmentModel.site_id.in_(owned_sites()),
        )
    )


def require_site(site_id):
    if not SiteModel.query.filter(SiteModel.id == site_id, SiteModel.id.in_(owned_sites())).first():
        abort(403, message="Forbidden")


def authorized_appointment(appointment_id):
    appointment = scoped_appointments(AppointmentModel.query).filter_by(id=appointment_id).first()
    if appointment is None:
        abort(404, message="Appointment not found")
    return appointment


def require_booking(data):
    actor = principal_id()
    if data["client_id"] != actor:
        require_site(data["site_id"])
    if UserModel.find_by_id(data["client_id"]) is None:
        abort(400, message="Invalid client")
    if not SiteModel.query.filter_by(id=data["site_id"]).first():
        abort(400, message="Invalid site")
    if not WorkerModel.query.filter_by(
        id=data["worker_id"], site_id=data["site_id"], active=True
    ).first():
        abort(400, message="Worker does not belong to site")


def require_manager():
    if ManagerModel.find_by_id(principal_id()) is None:
        abort(403, message="Manager identity required")


def tenant_write(model=None):
    """Authorize current and requested site for writes to site/worker resources."""

    def decorate(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            principal_id()
            body = request.get_json(silent=True) or request.form.to_dict()
            if not isinstance(body, dict):
                abort(400, message="Invalid body")
            data = dict(body)
            # Reject conflicting locations rather than authorizing one ID and writing another.
            for key in ("id", "site_id", "worker_id"):
                query_value = request.args.get(key)
                if query_value is not None:
                    if data.get(key) is not None and str(data[key]) != query_value:
                        abort(400, message="Conflicting resource identifiers")
                    data[key] = query_value
            sites = []
            if model is not None and data.get("id") is not None:
                item = model.query.filter_by(id=data["id"]).first()
                if item is not None:
                    if hasattr(item, "site_id"):
                        sites.append(item.site_id)
                    elif hasattr(item, "worker_id"):
                        worker = WorkerModel.query.filter_by(id=item.worker_id).first()
                        if worker:
                            sites.append(worker.site_id)
            if data.get("site_id") is not None:
                sites.append(data["site_id"])
            if data.get("worker_id") is not None:
                worker = WorkerModel.query.filter_by(id=data["worker_id"]).first()
                if worker is None:
                    abort(404, message="Worker not found")
                sites.append(worker.site_id)
            if not sites:
                abort(403, message="Site ownership required")
            for site_id in sites:
                require_site(site_id)
            return func(*args, **kwargs)

        return wrapped

    return decorate
