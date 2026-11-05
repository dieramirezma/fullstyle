import os
from datetime import datetime

from flask import render_template


class EmailService:
    def __init__(self):
        self.resend_api_key = os.environ.get("RESEND_API_KEY")
        self.resend_url = "https://api.resend.com/emails"
        self.from_email = "soporte@full-style.com"

    def send_email(self, to_email, subject, template_name, template_data):
        from services.durable_mail import delivery_context, record_delivery

        if os.getenv("LOCAL_RUNTIME") != "true" or os.getenv("DELIVERY_MODE") != "local":
            raise RuntimeError("External delivery is disabled in this environment")
        render_template(f"emails/{template_name}.html", **template_data)
        _, event_id, ordinal = delivery_context.get()
        result = {
            "id": f"{event_id}:{ordinal}",
            "to": to_email if isinstance(to_email, list) else [to_email],
            "subject": subject,
            "mode": "local",
            "requester": template_data.get("email"),
        }
        return record_delivery(result)

    def send_subscription_confirmation(
        self, owner_email, owner_name, subscription_plan, payment_date, finish_date
    ):
        template_data = {
            "owner_name": owner_name,
            "subscription_plan": subscription_plan,
            "payment_date": payment_date,
            "finish_date": finish_date,
        }

        return self.send_email(
            owner_email, "¡Tu suscripción a FullStyle está activa!", "subscription", template_data
        )

    def send_reset_password(self, email, name, reset_link=None):
        template_data = {"name": name, "email": email, "reset_link": reset_link}
        return self.send_email(email, "Recuperación de contraseña", "reset_password", template_data)

    def send_contact_email(self, name, email, message):
        # Send to support
        template_data = {
            "name": name,
            "email": email,
            "message": message,
            "current_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.send_email(
            "support@synthetic.invalid",
            "Contacto desde el sitio web FullStyle",
            "contact",
            template_data,
        )

        # Send auto-reply to user
        user_template_data = {"name": name}
        return self.send_email(
            email, "Gracias por contactarnos", "response_contact", user_template_data
        )

    def send_appointment_confirmation(
        self,
        customer_email,
        customer_name,
        site_name,
        site_address,
        site_phone,
        service_name,
        service_description,
        worker_name,
        appointment_date,
        appointment_time,
        service_price,
        service_duration,
    ):
        template_data = {
            "customerName": customer_name,
            "siteName": site_name,
            "siteAddress": site_address,
            "sitePhone": site_phone,
            "serviceName": service_name,
            "serviceDescription": service_description or "Sin descripción",
            "workerName": worker_name,
            "appointmentDate": appointment_date,
            "appointmentTime": appointment_time,
            "servicePrice": service_price,
            "serviceDuration": service_duration,
        }

        return self.send_email(
            customer_email, "Confirmación de tu Cita", "appointment_fullpaid", template_data
        )

    def send_partial_payment_confirmation(
        self,
        customer_email,
        customer_name,
        site_name,
        site_address,
        site_phone,
        service_name,
        service_description,
        worker_name,
        appointment_date,
        appointment_time,
        service_price,
        partial_payment,
        service_duration,
    ):
        template_data = {
            "customerName": customer_name,
            "siteName": site_name,
            "siteAddress": site_address,
            "sitePhone": site_phone,
            "serviceName": service_name,
            "serviceDescription": service_description or "Sin descripción",
            "workerName": worker_name,
            "appointmentDate": appointment_date,
            "appointmentTime": appointment_time,
            "servicePrice": service_price,
            "partialPayment": partial_payment,
            "serviceDuration": service_duration,
        }

        return self.send_email(
            customer_email,
            "Confirmación de Pago de Reserva",
            "appointment_partialpaid",
            template_data,
        )

    def send_appointment_rejected(
        self, customer_email, customer_name, appointment_date, appointment_time, service_price
    ):
        template_data = {
            "customerName": customer_name,
            "appointmentDate": appointment_date,
            "appointmentTime": appointment_time,
            "servicePrice": service_price,
        }

        return self.send_email(
            customer_email,
            "Pago rechazado - No se agendó tu cita",
            "appointment_rejected",
            template_data,
        )

    def send_appointment_canceled(
        self,
        customer_email,
        customer_name,
        site_name,
        site_address,
        site_phone,
        service_name,
        worker_name,
        appointment_date,
        appointment_time,
    ):
        template_data = {
            "customerName": customer_name,
            "siteName": site_name,
            "siteAddress": site_address,
            "sitePhone": site_phone,
            "serviceName": service_name,
            "workerName": worker_name,
            "appointmentDate": appointment_date,
            "appointmentTime": appointment_time,
        }

        return self.send_email(
            customer_email, "Cita cancelada - FullStyle", "appointment_canceled", template_data
        )
