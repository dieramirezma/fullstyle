import logging
import os

logger = logging.getLogger(__name__)

# Get the Email Service URL from environment variables
EMAIL_SERVICE_URL = os.environ.get(
    "EMAIL_SERVICE_URL", "http://localhost:5001"
)  # Default for local dev


class EmailProducer:
    def __init__(self):
        # No longer needs self.queue_name
        pass

    def _send_request_to_email_service(self, endpoint, data):
        from flask import g

        from utils.mail_outbox import enqueue_mail

        kinds = {
            "subscription": "subscription",
            "reset-password": "reset_password",
            "contact": "contact",
            "appointment/confirmation": "appointment_confirmation",
            "appointment/partial-payment": "partial_payment_confirmation",
            "appointment/rejected": "appointment_rejected",
            "appointment/canceled": "appointment_canceled",
        }
        kind = kinds[endpoint.removeprefix("/api/emails/")]
        event_id = enqueue_mail(kind, data, correlation_id=g.correlation_id)
        return {"message": "Email task queued successfully", "event_id": event_id}

    def send_subscription_email(
        self, owner_email, owner_name, subscription_plan, payment_date, finish_date
    ):
        payload = {
            "owner_email": owner_email,
            "owner_name": owner_name,
            "subscription_plan": subscription_plan,
            "payment_date": payment_date,
            "finish_date": finish_date,
        }
        return self._send_request_to_email_service("/api/emails/subscription", payload)

    def send_reset_password_email(self, email, name):
        payload = {"email": email, "name": name}
        return self._send_request_to_email_service("/api/emails/reset-password", payload)

    def send_contact_email(self, name, email, message):
        payload = {"name": name, "email": email, "message": message}
        return self._send_request_to_email_service("/api/emails/contact", payload)

    def send_appointment_confirmation(self, **kwargs):
        return self._send_request_to_email_service("/api/emails/appointment/confirmation", kwargs)

    def send_partial_payment_confirmation(self, **kwargs):
        return self._send_request_to_email_service(
            "/api/emails/appointment/partial-payment", kwargs
        )

    def send_appointment_rejected(self, **kwargs):
        return self._send_request_to_email_service("/api/emails/appointment/rejected", kwargs)

    def send_appointment_canceled(self, **kwargs):
        return self._send_request_to_email_service("/api/emails/appointment/canceled", kwargs)
