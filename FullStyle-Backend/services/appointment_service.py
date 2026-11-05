from flask_jwt_extended import jwt_required
from flask_restful import Resource, reqparse, request

from config.db_config import db
from models.appointment_model import AppointmentModel
from models.consistency_model import BookingTerms, PaymentIntent
from models.detail_model import DetailModel
from models.payment_model import PaymentModel
from models.service_model import ServiceModel
from models.site_model import SiteModel
from utils.authorization import require_booking, require_site, scoped_appointments
from utils.booking_consistency import (
    lock_appointment,
    lock_service_terms,
    lock_workers,
    snapshot_terms,
    transactional,
)
from utils.cache_helper import CACHE_TTL, cache_result
from utils.helpers import (
    check_appointment_time,
    compute_appointment_statistics,
    is_worker_available,
)


class Appointment(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("id", type=int, required=False)
    parser.add_argument(
        "appointmenttime", type=str, required=True, help="This field cannot be left blank!"
    )
    parser.add_argument("status", type=str, required=False, default="pending")
    parser.add_argument(
        "worker_id", type=int, required=True, help="This field cannot be left blank!"
    )
    parser.add_argument("site_id", type=int, required=True, help="This field cannot be left blank!")
    parser.add_argument(
        "service_id", type=int, required=True, help="This field cannot be left blank!"
    )
    parser.add_argument(
        "client_id", type=int, required=True, help="This field cannot be left blank!"
    )
    parser.add_argument("request", type=int, required=False, default=False)

    @jwt_required()
    @cache_result(ttl=CACHE_TTL["appointments"], namespace="appointments", private=True)
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, location="args", required=False)
        parser.add_argument("status", type=str, location="args", required=False)
        parser.add_argument("worker_id", type=int, location="args", required=False)
        parser.add_argument("site_id", type=int, location="args", required=False)
        parser.add_argument("service_id", type=int, location="args", required=False)
        parser.add_argument("client_id", type=int, location="args", required=False)
        args = parser.parse_args()

        query = scoped_appointments(AppointmentModel.query)

        if args["id"]:
            query = query.filter_by(id=args["id"])

        if args["status"]:
            query = query.filter_by(status=args["status"])

        if args["worker_id"]:
            query = query.filter_by(worker_id=args["worker_id"])

        if args["site_id"]:
            query = query.filter_by(site_id=args["site_id"])

        if args["service_id"]:
            query = query.filter_by(service_id=args["service_id"])

        if args["client_id"]:
            query = query.filter_by(client_id=args["client_id"])

        appointments = query.all()

        if appointments:
            appointments_json = [appointment.json() for appointment in appointments]
            return appointments_json, 200
        return {"message": "Appointment not found"}, 404

    @jwt_required()
    @transactional
    def post(self):
        data = Appointment.parser.parse_args()
        require_booking(data)
        if data["status"] != "pending":
            return {
                "message": "New bookings must be pending; payment requires verified events"
            }, 403
        lock_workers(data["worker_id"])
        # Recheck mutable worker/site membership after acquiring the lock.
        require_booking(data)
        lock_service_terms(data["site_id"], data["service_id"])
        appointmenttime, error = check_appointment_time(data["appointmenttime"])
        if error:
            return {"message": error}, 400
        available, message = is_worker_available(
            data["worker_id"], appointmenttime.date(), appointmenttime.time(), data["service_id"]
        )
        if not available:
            return {"message": message}, 409 if "overlapping" in message else 400
        if data["request"]:
            return True, 200
        appointment = AppointmentModel(
            appointmenttime=appointmenttime,
            status="pending",
            worker_id=data["worker_id"],
            site_id=data["site_id"],
            service_id=data["service_id"],
            client_id=data["client_id"],
        )
        db.session.add(appointment)
        db.session.flush()
        snapshot_terms(appointment)
        return appointment.json(), 201

    @jwt_required()
    @transactional
    def put(self):
        data = Appointment.parser.parse_args()
        if not data["id"]:
            return {"message": "Appointment ID is required"}, 400
        appointment = lock_appointment(data["id"])
        if data["client_id"] != appointment.client_id:
            return {"message": "Appointment client cannot be reassigned"}, 403
        lock_workers(appointment.worker_id, data["worker_id"])
        require_booking(data)
        if data["status"] not in {"pending", "cancelled", "canceled"}:
            return {"message": "Financial states require verified payment events"}, 403
        if (
            PaymentIntent.query.filter_by(appointment_id=appointment.id).first()
            or appointment.status == "paid"
            or PaymentModel.query.filter_by(appointment_id=appointment.id).first()
        ):
            return {
                "message": "Booking with a payment intent is immutable; settlement/refund required"
            }, 409
        lock_service_terms(data["site_id"], data["service_id"])
        appointmenttime, error = check_appointment_time(data["appointmenttime"])
        if error:
            return {"message": error}, 400
        if data["status"] == "pending":
            available, message = is_worker_available(
                data["worker_id"],
                appointmenttime.date(),
                appointmenttime.time(),
                data["service_id"],
                current_appointment_id=appointment.id,
            )
            if not available:
                return {"message": message}, 409 if "overlapping" in message else 400
        changed_service = (appointment.site_id, appointment.service_id) != (
            data["site_id"],
            data["service_id"],
        )
        if changed_service:
            terms = db.session.get(BookingTerms, appointment.id)
            if terms:
                db.session.delete(terms)
                db.session.flush()
        for field in ("worker_id", "site_id", "service_id", "client_id", "status"):
            setattr(appointment, field, data[field])
        appointment.appointmenttime = appointmenttime
        snapshot_terms(appointment)
        return appointment.json(), 200

    @jwt_required()
    @transactional
    def delete(self):
        appointment_id = request.args.get("id", type=int)
        if not appointment_id:
            return {"message": "Appointment ID is required as a query parameter"}, 400
        appointment = lock_appointment(appointment_id)
        lock_workers(appointment.worker_id)
        if (
            PaymentIntent.query.filter_by(appointment_id=appointment.id).first()
            or appointment.status == "paid"
            or PaymentModel.query.filter_by(appointment_id=appointment.id).first()
        ):
            return {"message": "Booking with a payment intent cannot be deleted"}, 409
        db.session.delete(appointment)
        return {"message": "Appointment deleted"}, 200


class AppointmentDetail(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("id", type=int, required=False)
    parser.add_argument(
        "appointmenttime", type=str, required=True, help="This field cannot be left blank!"
    )
    parser.add_argument("status", type=str, required=False, default="pending")
    parser.add_argument(
        "worker_id", type=int, required=True, help="This field cannot be left blank!"
    )
    parser.add_argument("site_id", type=int, required=True, help="This field cannot be left blank!")
    parser.add_argument(
        "service_id", type=int, required=True, help="This field cannot be left blank!"
    )
    parser.add_argument(
        "client_id", type=int, required=True, help="This field cannot be left blank!"
    )

    @jwt_required()
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, location="args", required=False)
        parser.add_argument("status", type=str, location="args", required=False)
        parser.add_argument("worker_id", type=int, location="args", required=False)
        parser.add_argument("site_id", type=int, location="args", required=False)
        parser.add_argument("service_id", type=int, location="args", required=False)
        parser.add_argument("client_id", type=int, location="args", required=False)
        args = parser.parse_args()

        query = scoped_appointments(AppointmentModel.query)

        if args["id"]:
            query = query.filter_by(id=args["id"])
        if args["status"]:
            query = query.filter_by(status=args["status"])
        if args["worker_id"]:
            query = query.filter_by(worker_id=args["worker_id"])
        if args["site_id"]:
            query = query.filter_by(site_id=args["site_id"])
        if args["service_id"]:
            query = query.filter_by(service_id=args["service_id"])
        if args["client_id"]:
            query = query.filter_by(client_id=args["client_id"])

        appointments = query.all()

        if not appointments:
            return {"message": "Appointment not found"}, 404

        appointments_json = []
        for appt in appointments:
            # Start with the appointment data
            data = appt.json()
            # Save the id values before removing them
            site_id = data.get("site_id")
            service_id = data.get("service_id")
            data.pop("worker_id", None)
            data.pop("site_id", None)
            data.pop("service_id", None)

            # Expand worker attributes using the relationship
            data["worker"] = appt.worker.json() if appt.worker else {}

            # Query for the site information
            site = SiteModel.query.filter_by(id=site_id).first()
            data["site"] = site.json() if site and hasattr(site, "json") else {}

            # Query for the service information
            detail = DetailModel.query.filter_by(site_id=site_id, service_id=service_id).first()
            service_data = detail.json() if detail and hasattr(detail, "json") else {}
            service = ServiceModel.find_by_id(service_id)
            if service:
                service_data = {"name": service.name, **service_data}
            data["service"] = service_data

            appointments_json.append(data)

        return appointments_json, 200


# How many appointments have been made with an specific worker in a site
class AppointmentWorkerStatistics(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument(
        "site_id", type=int, required=True, location="args", help="site_id is required"
    )
    parser.add_argument(
        "period",
        type=str,
        required=False,
        default="total",
        location="args",
        help="Period can be total, daily, weekly, monthly",
    )
    parser.add_argument(
        "count_periods",
        type=int,
        required=False,
        default=0,
        location="args",
        help="Number of days/weeks/months to include from current date backwards if > 0",
    )

    @jwt_required()
    def get(self):
        args = AppointmentWorkerStatistics.parser.parse_args()
        site_id = args["site_id"]
        require_site(site_id)
        period = args["period"].lower()
        count_periods = args["count_periods"]

        results = compute_appointment_statistics(
            site_id, period, count_periods, AppointmentModel.worker_id
        )

        # Format results
        stats = []
        if period == "total" and type(results) is dict:
            stats = results
        else:
            for item in results:
                record = {"worker_id": item.worker_id, "total": item.total}
                if period == "daily":
                    record["day"] = item.day.strftime("%Y-%m-%d")
                elif period == "weekly":
                    record["week_start"] = item.week_start.strftime("%Y-%m-%d")
                elif period == "monthly":
                    record["year"] = int(item.year)
                    record["month"] = int(item.month)
                stats.append(record)

        return {
            "site_id": site_id,
            "period": period,
            "count_periods": count_periods,
            "statistics": stats,
        }, 200


# How many appointments have been made in a site
class AppointmentSiteStatistics(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument(
        "site_id", type=int, required=True, location="args", help="site_id is required"
    )
    parser.add_argument(
        "period",
        type=str,
        required=False,
        default="total",
        location="args",
        help="Period can be total, daily, weekly, or monthly",
    )
    parser.add_argument(
        "count_periods",
        type=int,
        required=False,
        default=0,
        location="args",
        help="Number of days/weeks/months to include from current date backwards if > 0",
    )

    @jwt_required()
    def get(self):
        args = AppointmentSiteStatistics.parser.parse_args()
        site_id = args["site_id"]
        require_site(site_id)
        period = args["period"].lower()
        count_periods = args["count_periods"]

        results = compute_appointment_statistics(site_id, period, count_periods, group_column=None)

        # Format results
        if period == "total" and isinstance(results, dict):
            stats = results
        elif period == "daily":
            stats = [{"day": r.day.strftime("%Y-%m-%d"), "total": r.total} for r in results]
        elif period == "weekly":
            stats = [
                {"week_start": r.week_start.strftime("%Y-%m-%d"), "total": r.total} for r in results
            ]
        elif period == "monthly":
            stats = [
                {"year": int(r.year), "month": int(r.month), "total": r.total} for r in results
            ]
        else:
            return {"message": "Invalid period parameter. Use total, daily, weekly or monthly"}, 400

        return {
            "site_id": site_id,
            "period": period,
            "count_periods": count_periods,
            "statistics": stats,
        }, 200


# How many appointments have been made for each service in a site
class AppointmentServiceStatistics(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument(
        "site_id", type=int, required=True, location="args", help="site_id is required"
    )
    parser.add_argument(
        "period",
        type=str,
        required=False,
        default="total",
        location="args",
        help="Period can be total, daily, weekly, or monthly",
    )
    parser.add_argument(
        "count_periods",
        type=int,
        required=False,
        default=0,
        location="args",
        help="Number of days/weeks/months to include from current date backwards if > 0",
    )

    @jwt_required()
    def get(self):
        args = AppointmentServiceStatistics.parser.parse_args()
        site_id = args["site_id"]
        require_site(site_id)
        period = args["period"].lower()
        count_periods = args["count_periods"]

        results = compute_appointment_statistics(
            site_id, period, count_periods, AppointmentModel.service_id
        )

        # Format results
        if period == "total" and isinstance(results, dict):
            stats = results
        elif period == "daily":
            stats = [
                {"service_id": r.service_id, "day": r.day.strftime("%Y-%m-%d"), "total": r.total}
                for r in results
            ]
        elif period == "weekly":
            stats = [
                {
                    "service_id": r.service_id,
                    "week_start": r.week_start.strftime("%Y-%m-%d"),
                    "total": r.total,
                }
                for r in results
            ]
        elif period == "monthly":
            stats = [
                {
                    "service_id": r.service_id,
                    "year": int(r.year),
                    "month": int(r.month),
                    "total": r.total,
                }
                for r in results
            ]
        else:
            return {"message": "Invalid period parameter. Use total, daily, weekly or monthly"}, 400

        return {
            "site_id": site_id,
            "period": period,
            "count_periods": count_periods,
            "statistics": stats,
        }, 200
