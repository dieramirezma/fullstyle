def compute_daily_schedule(worker, date):
    weekday = date.strftime('%A')
    dayoff = DaysOffModel.query.filter_by(worker_id=worker.id, dayoff=date).first()
    if dayoff:
        return {'available': [], 'occupied': []}
    seasonal_schedule = SeasonalScheduleModel.query.filter(SeasonalScheduleModel.worker_id == worker.id, SeasonalScheduleModel.startdate <= date, SeasonalScheduleModel.enddate >= date).first()
    available = []
    if seasonal_schedule:
        available.append({'start': str(seasonal_schedule.starttime), 'end': str(seasonal_schedule.endtime)})
    else:
        slots = AvailabilityModel.query.filter_by(worker_id=worker.id, weekday=weekday).all()
        for slot in slots:
            available.append({'start': str(slot.starttime), 'end': str(slot.endtime)})
    appointments = AppointmentModel.query.filter(AppointmentModel.worker_id == worker.id, func.date(AppointmentModel.appointmenttime) == date).all()
    occupied = []
    for appointment in appointments:
        detail = DetailModel.query.filter_by(site_id=worker.site_id, service_id=appointment.service_id).first()
        if detail:
            end_time = (appointment.appointmenttime + timedelta(minutes=detail.duration)).time()
            occupied.append({'start': str(appointment.appointmenttime.time()), 'end': str(end_time)})
    return {'available': available, 'occupied': occupied}
