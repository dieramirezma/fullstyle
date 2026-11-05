-- Worker equality + timestamp range, excluding cancelled appointments.
CREATE INDEX ix_appointment_worker_time_active ON appointment(worker_id,appointmenttime)
WHERE status NOT IN ('cancelled','canceled');
