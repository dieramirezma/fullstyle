from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from sqlalchemy import func, or_

from models.appointment_model import AppointmentModel
from models.availability_model import AvailabilityModel
from models.category_model import CategoryModel
from models.days_off_model import DaysOffModel
from models.detail_model import DetailModel
from models.manager_model import ManagerModel
from models.payment_model import PaymentModel
from models.seasonal_schedule_model import SeasonalScheduleModel
from models.service_model import ServiceModel
from models.site_has_category_model import SiteHasCategoryModel
from models.site_model import SiteModel
from models.worker_has_service_model import WorkerHasServiceModel
from models.worker_model import WorkerModel

#
#   Helpers for appointment
#


def check_worker_exists(worker_id):
    worker = WorkerModel.query.filter_by(id=worker_id).first()
    if not worker:
        return None, "Worker not found"
    return worker, None


def check_worker_active(worker_id):
    worker = WorkerModel.query.filter_by(id=worker_id, active=True).first()
    if not worker:
        return None, "Worker not found or inactive"
    return worker, None


def check_appointment_time(appointment_time_str):
    try:
        date = datetime.strptime(appointment_time_str, "%Y-%m-%dT%H:%M:%S")
        return date, None
    except ValueError:
        return None, "Invalid date format. Use 'YYYY-MM-DDTHH:MM:SS'."


def check_worker_day_off(worker_id, date):
    dayoff = DaysOffModel.query.filter_by(worker_id=worker_id, dayoff=date).first()
    if dayoff:
        return False, "Worker is not available on this day"
    return True, None


def check_seasonal_schedule(worker_id, date, time):
    seasonal_schedule = SeasonalScheduleModel.query.filter(
        SeasonalScheduleModel.worker_id == worker_id,
        SeasonalScheduleModel.startdate <= date,
        SeasonalScheduleModel.enddate >= date,
    ).first()
    if seasonal_schedule:
        if seasonal_schedule.starttime <= time <= seasonal_schedule.endtime:
            return seasonal_schedule, None
        else:
            return None, "Worker is not available at this time"
    return None, None


def check_regular_availability(worker_id, date, time):
    weekday = date.strftime("%A")
    availability = AvailabilityModel.query.filter_by(worker_id=worker_id, weekday=weekday).all()
    for slot in availability:
        if slot.starttime <= time <= slot.endtime:
            return slot, None
    return None, "Worker is not available at this time"


def check_service_detail(worker, service_id):
    detail = DetailModel.query.filter_by(site_id=worker.site_id, service_id=service_id).first()
    if not detail:
        return None, "Service detail not found"
    return detail, None


def check_appointment_exists(appointment_id):
    appointment = AppointmentModel.find_by_id(appointment_id)
    if not appointment:
        return None, "Appointment not found"
    return appointment, None


#
#   Helpers for availability
#


def check_availability_exists(availability_id):
    availability = AvailabilityModel.query.filter_by(id=availability_id).first()
    if not availability:
        return None, "Availability not found"
    return availability, None


# Have to check if it doesn't conflict with updating the same register of availability
def check_overlapping_availability(
    worker_id, weekday, starttime, endtime, current_availability_id=None
):
    overlapping_availability = AvailabilityModel.query.filter(
        AvailabilityModel.worker_id == worker_id,
        AvailabilityModel.weekday == weekday,
        AvailabilityModel.starttime < endtime,
        AvailabilityModel.endtime > starttime,
        AvailabilityModel.id != current_availability_id,
    ).first()
    if overlapping_availability:
        return False, f"Overlapping availability found id={overlapping_availability.id}"
    return True, None


#
#   Helpers for days off
#


def check_date(date_str):
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        return date, None
    except ValueError:
        return None, "Invalid date format. Use 'YYYY-MM-DD'."


def check_dayoff_exists(dayoff_id):
    dayoff = DaysOffModel.query.filter_by(id=dayoff_id).first()
    if not dayoff:
        return None, "Day off not found"
    return dayoff, None


#
#   Helpers for detail
#


def check_detail_exists(site_id, service_id):
    detail = DetailModel.query.filter_by(site_id=site_id, service_id=service_id).first()
    if not detail:
        return None, "Detail not found"
    return detail, None


def check_detail_active(site_id, service_id):
    detail = DetailModel.query.filter_by(
        site_id=site_id, service_id=service_id, active=True
    ).first()
    if not detail:
        return None, "Detail not found or inactive"
    return detail, None


def check_price(price):
    if not isinstance(price, int) or price < 0:
        return False, "Invalid price. Price must be a non-negative integer."
    return True, None


def check_duration(duration):
    if not isinstance(duration, int) or duration <= 0:
        return False, "Invalid duration. Duration must be a positive integer."
    return True, None


#
#   Helpers for seasonal_schedule
#


def check_time(time_str):
    try:
        time = datetime.strptime(time_str, "%H:%M:%S").time()
        return time, None
    except ValueError:
        return None, "Invalid time format. Use 'HH:MM:SS'."


def check_seasonal_schedule_exists(seasonal_schedule_id):
    seasonal_schedule = SeasonalScheduleModel.query.filter_by(id=seasonal_schedule_id).first()
    if not seasonal_schedule:
        return None, "Seasonal schedule not found"
    return seasonal_schedule, None


#
#   Helpers for service
#


def check_category_exists(category_id):
    category = CategoryModel.query.filter_by(id=category_id).first()
    if not category:
        return None, "Category not found"
    return category, None


def check_service_unique(name, category_id):
    service = ServiceModel.query.filter_by(name=name, category_id=category_id).first()
    if service:
        return False, "Service with the same name and category already exists"
    return True, None


#
#   Helpers for site_has_service
#


def check_site_exists(site_id):
    site = SiteModel.query.filter_by(id=site_id).first()
    if not site:
        return None, "Site not found"
    return site, None


def check_site_category_exists(site_id, category_id):
    site_category = SiteHasCategoryModel.query.filter_by(
        site_id=site_id, category_id=category_id
    ).first()
    if site_category:
        return False, "Site-Category relationship already exists"
    return True, None


#
#   Helpers for site
#


def check_manager_exists(manager_id):
    manager = ManagerModel.query.filter_by(id=manager_id).first()
    if not manager:
        return None, "Manager not found"
    return manager, None


def check_phone(phone):
    if not isinstance(phone, int) or phone <= 0:
        return False, "Invalid phone number. Phone number must be a positive integer."
    return True, None


#
#   Helpers for worker_has_service
#


def check_service_allowed_for_site(site_id, service_id):
    site_service = DetailModel.query.filter_by(site_id=site_id, service_id=service_id).first()
    if not site_service:
        return False, "Service not allowed for this worker's site"
    return True, None


def check_worker_service_exists(worker_id, service_id):
    worker_service = WorkerHasServiceModel.query.filter_by(
        worker_id=worker_id, service_id=service_id
    ).first()
    if worker_service:
        return False, "Worker-Service relationship already exists"
    return True, None


#
#   Helpers for worker
#


def check_overlapping_appointments(
    worker, worker_id, service_id, date, time, schedule, current_appointment_id=None
):
    from models.consistency_model import BookingTerms

    detail, error = check_service_detail(worker, service_id)
    if error or not detail.active or detail.duration <= 0:
        return False, error or "Invalid service terms"
    duration = detail.duration
    if current_appointment_id:
        current = AppointmentModel.find_by_id(current_appointment_id)
        terms = BookingTerms.query.filter_by(appointment_id=current_appointment_id).first()
        if (
            current
            and terms
            and (current.site_id, current.service_id) == (worker.site_id, service_id)
        ):
            duration = terms.duration
    start = datetime.combine(date, time)
    end = start + timedelta(minutes=duration)
    if end > datetime.combine(date, schedule.endtime):
        return False, "Worker is not available for the full duration of the service"
    # Full interval intersection, including long and cross-midnight legacy bookings.
    # The caller holds the worker row lock until the write commits.
    effective_duration = func.coalesce(BookingTerms.duration, DetailModel.duration)
    overlap = (
        AppointmentModel.query.outerjoin(
            BookingTerms, BookingTerms.appointment_id == AppointmentModel.id
        )
        .outerjoin(
            DetailModel,
            (DetailModel.site_id == AppointmentModel.site_id)
            & (DetailModel.service_id == AppointmentModel.service_id),
        )
        .filter(
            AppointmentModel.worker_id == worker_id,
            AppointmentModel.status.notin_(["cancelled", "canceled"]),
            AppointmentModel.appointmenttime < end,
            AppointmentModel.appointmenttime + func.make_interval(0, 0, 0, 0, 0, effective_duration)
            > start,
        )
    )
    unresolved = (
        AppointmentModel.query.outerjoin(
            BookingTerms, BookingTerms.appointment_id == AppointmentModel.id
        )
        .outerjoin(
            DetailModel,
            (DetailModel.site_id == AppointmentModel.site_id)
            & (DetailModel.service_id == AppointmentModel.service_id),
        )
        .filter(
            AppointmentModel.worker_id == worker_id,
            AppointmentModel.status.notin_(["cancelled", "canceled"]),
            or_(effective_duration.is_(None), effective_duration <= 0),
        )
    )
    if unresolved.first():
        return False, "Worker has an overlapping appointment or unresolved legacy duration"
    if current_appointment_id is not None:
        overlap = overlap.filter(AppointmentModel.id != current_appointment_id)
    if overlap.first():
        return False, "Worker has an overlapping appointment"
    return True, "Worker is available"


def is_worker_available(worker_id, date, time, service_id, current_appointment_id=None):
    # Check if the worker is active
    worker, error = check_worker_active(worker_id)
    if error:
        return False, error

    # Check if the worker has a day off
    available, error = check_worker_day_off(worker_id, date)
    if not available:
        return False, error

    # Check if the worker has a seasonal schedule
    seasonal_schedule, error = check_seasonal_schedule(worker_id, date, time)
    if seasonal_schedule:
        return check_overlapping_appointments(
            worker, worker_id, service_id, date, time, seasonal_schedule, current_appointment_id
        )
    elif error:
        return False, error

    # Check the worker's regular availability
    slot, error = check_regular_availability(worker_id, date, time)
    if slot:
        return check_overlapping_appointments(
            worker, worker_id, service_id, date, time, slot, current_appointment_id
        )
    else:
        return False, error


def compute_daily_schedule(worker, date):
    from models.consistency_model import BookingTerms

    weekday = date.strftime("%A")
    # Check if worker has a day off
    dayoff = DaysOffModel.query.filter_by(worker_id=worker.id, dayoff=date).first()
    if dayoff:
        return {"available": [], "occupied": []}

    # Get the worker's seasonal schedules
    seasonal_schedule = SeasonalScheduleModel.query.filter(
        SeasonalScheduleModel.worker_id == worker.id,
        SeasonalScheduleModel.startdate <= date,
        SeasonalScheduleModel.enddate >= date,
    ).first()

    # Initialize the available list
    available = []
    if seasonal_schedule:
        available.append(
            {"start": str(seasonal_schedule.starttime), "end": str(seasonal_schedule.endtime)}
        )
    else:
        # Get the worker's regular availability
        slots = AvailabilityModel.query.filter_by(worker_id=worker.id, weekday=weekday).all()
        for slot in slots:
            available.append({"start": str(slot.starttime), "end": str(slot.endtime)})

    # One bounded query replaces two per-booking lookups; range uses the worker index.
    day_start = datetime.combine(date, datetime.min.time())
    appointments = (
        AppointmentModel.query.with_entities(
            AppointmentModel.appointmenttime,
            func.coalesce(BookingTerms.duration, DetailModel.duration).label("duration"),
        )
        .join(
            DetailModel,
            (DetailModel.site_id == worker.site_id)
            & (DetailModel.service_id == AppointmentModel.service_id),
        )
        .outerjoin(BookingTerms, BookingTerms.appointment_id == AppointmentModel.id)
        .filter(
            AppointmentModel.worker_id == worker.id,
            AppointmentModel.status.notin_(["cancelled", "canceled"]),
            AppointmentModel.appointmenttime >= day_start,
            AppointmentModel.appointmenttime < day_start + timedelta(days=1),
        )
        .order_by(AppointmentModel.id)
        .all()
    )
    occupied = []
    for appointment in appointments:
        end_time = (appointment.appointmenttime + timedelta(minutes=appointment.duration)).time()
        occupied.append({"start": str(appointment.appointmenttime.time()), "end": str(end_time)})
    return {"available": available, "occupied": occupied}


#
#   Helpers for appointment and payment statistics
#


def compute_appointment_statistics(site_id, period, count_periods, group_column=None):
    now = datetime.now()

    if count_periods > 0:
        if period == "daily":
            start_date = now - timedelta(days=count_periods)
        elif period == "weekly":
            start_date = now - timedelta(weeks=count_periods)
        elif period == "monthly":
            start_date = now - relativedelta(months=count_periods)
        else:
            start_date = None
    else:
        start_date = None

    base_query = AppointmentModel.query.filter(AppointmentModel.site_id == site_id)
    if start_date:
        base_query = base_query.filter(
            AppointmentModel.appointmenttime >= start_date, AppointmentModel.appointmenttime <= now
        )

    if period == "total":
        if group_column:
            results = (
                base_query.with_entities(
                    group_column, func.count(AppointmentModel.id).label("total")
                )
                .group_by(group_column)
                .all()
            )
        else:
            total = base_query.count()
            return {"total": total}
    elif period == "daily":
        if group_column:
            results = (
                base_query.with_entities(
                    group_column,
                    func.date(AppointmentModel.appointmenttime).label("day"),
                    func.count(AppointmentModel.id).label("total"),
                )
                .group_by(group_column, func.date(AppointmentModel.appointmenttime))
                .all()
            )
        else:
            results = (
                base_query.with_entities(
                    func.date(AppointmentModel.appointmenttime).label("day"),
                    func.count(AppointmentModel.id).label("total"),
                )
                .group_by(func.date(AppointmentModel.appointmenttime))
                .all()
            )
    elif period == "weekly":
        if group_column:
            results = (
                base_query.with_entities(
                    group_column,
                    func.date_trunc("week", AppointmentModel.appointmenttime).label("week_start"),
                    func.count(AppointmentModel.id).label("total"),
                )
                .group_by(group_column, func.date_trunc("week", AppointmentModel.appointmenttime))
                .all()
            )
        else:
            results = (
                base_query.with_entities(
                    func.date_trunc("week", AppointmentModel.appointmenttime).label("week_start"),
                    func.count(AppointmentModel.id).label("total"),
                )
                .group_by(func.date_trunc("week", AppointmentModel.appointmenttime))
                .all()
            )
    elif period == "monthly":
        if group_column:
            results = (
                base_query.with_entities(
                    group_column,
                    func.extract("year", AppointmentModel.appointmenttime).label("year"),
                    func.extract("month", AppointmentModel.appointmenttime).label("month"),
                    func.count(AppointmentModel.id).label("total"),
                )
                .group_by(
                    group_column,
                    func.extract("year", AppointmentModel.appointmenttime),
                    func.extract("month", AppointmentModel.appointmenttime),
                )
                .all()
            )
        else:
            results = (
                base_query.with_entities(
                    func.extract("year", AppointmentModel.appointmenttime).label("year"),
                    func.extract("month", AppointmentModel.appointmenttime).label("month"),
                    func.count(AppointmentModel.id).label("total"),
                )
                .group_by(
                    func.extract("year", AppointmentModel.appointmenttime),
                    func.extract("month", AppointmentModel.appointmenttime),
                )
                .all()
            )
    else:
        raise ValueError("Invalid period parameter. Use total, daily, weekly or monthly.")

    return results


def compute_payment_statistics(site_id, period, count_periods, group_column=None):
    now = datetime.now()
    if count_periods > 0:
        if period == "daily":
            start_date = now - timedelta(days=count_periods)
        elif period == "weekly":
            start_date = now - timedelta(weeks=count_periods)
        elif period == "monthly":
            start_date = now - relativedelta(months=count_periods)
        else:
            start_date = None
    else:
        start_date = None

    # Unir Payment con Appointment para filtrar por site_id
    base_query = PaymentModel.query.join(
        AppointmentModel, PaymentModel.appointment_id == AppointmentModel.id
    ).filter(AppointmentModel.site_id == site_id)

    if start_date:
        base_query = base_query.filter(
            PaymentModel.timestamp >= start_date, PaymentModel.timestamp <= now
        )

    if period == "total":
        if group_column:
            results = (
                base_query.with_entities(
                    group_column, func.sum(PaymentModel.amount).label("total_amount")
                )
                .group_by(group_column)
                .all()
            )
        else:
            total = (
                base_query.with_entities(
                    func.sum(PaymentModel.amount).label("total_amount")
                ).scalar()
                or 0
            )
            return {"total_amount": total}
    elif period == "daily":
        if group_column:
            results = (
                base_query.with_entities(
                    group_column,
                    func.date(PaymentModel.timestamp).label("day"),
                    func.sum(PaymentModel.amount).label("total_amount"),
                )
                .group_by(group_column, func.date(PaymentModel.timestamp))
                .all()
            )
        else:
            results = (
                base_query.with_entities(
                    func.date(PaymentModel.timestamp).label("day"),
                    func.sum(PaymentModel.amount).label("total_amount"),
                )
                .group_by(func.date(PaymentModel.timestamp))
                .all()
            )
    elif period == "weekly":
        if group_column:
            results = (
                base_query.with_entities(
                    group_column,
                    func.date_trunc("week", PaymentModel.timestamp).label("week_start"),
                    func.sum(PaymentModel.amount).label("total_amount"),
                )
                .group_by(group_column, func.date_trunc("week", PaymentModel.timestamp))
                .all()
            )
        else:
            results = (
                base_query.with_entities(
                    func.date_trunc("week", PaymentModel.timestamp).label("week_start"),
                    func.sum(PaymentModel.amount).label("total_amount"),
                )
                .group_by(func.date_trunc("week", PaymentModel.timestamp))
                .all()
            )
    elif period == "monthly":
        if group_column:
            results = (
                base_query.with_entities(
                    group_column,
                    func.extract("year", PaymentModel.timestamp).label("year"),
                    func.extract("month", PaymentModel.timestamp).label("month"),
                    func.sum(PaymentModel.amount).label("total_amount"),
                )
                .group_by(
                    group_column,
                    func.extract("year", PaymentModel.timestamp),
                    func.extract("month", PaymentModel.timestamp),
                )
                .all()
            )
        else:
            results = (
                base_query.with_entities(
                    func.extract("year", PaymentModel.timestamp).label("year"),
                    func.extract("month", PaymentModel.timestamp).label("month"),
                    func.sum(PaymentModel.amount).label("total_amount"),
                )
                .group_by(
                    func.extract("year", PaymentModel.timestamp),
                    func.extract("month", PaymentModel.timestamp),
                )
                .all()
            )
    else:
        raise ValueError("Invalid period parameter. Use total, daily, weekly or monthly.")

    return results
