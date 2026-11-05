import asyncio
import logging
from typing import Any, Dict, List, Optional, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.domain.tools.common import business_logic_api


class GetAppointmentDetailInput(BaseModel):
    id: Optional[int] = Field(
        None, description="ID específico de la cita para obtener detalles completos."
    )
    status: Optional[str] = Field(
        None,
        description="Estado de la cita para filtrar (pending, confirmed, canceled, completed).",
    )
    worker_id: Optional[int] = Field(
        None, description="ID del trabajador para ver detalles de todas sus citas."
    )
    site_id: Optional[int] = Field(
        None,
        description="ID del sitio para ver detalles de todas las citas de este lugar.",
    )
    service_id: Optional[int] = Field(
        None,
        description="ID del servicio para ver detalles de todas las citas de este tipo.",
    )
    client_id: Optional[int] = Field(
        None, description="ID del cliente para ver detalles de todas sus citas."
    )


class GetAppointmentDetailTool(BaseTool):
    name: str = "get_appointment_details"
    description: str = (
        "Útil para obtener información COMPLETA y DETALLADA de citas, incluyendo nombres de trabajador, sitio y servicio, "
        "además de descripciones, precios, duración, direcciones y fotos. "
        "Perfecto para mostrar resúmenes finales de citas o dar información completa al cliente. "
        "Más rico en información que get_appointments básico."
    )
    args_schema: Type[BaseModel] = GetAppointmentDetailInput

    def _run(
        self,
        id: Optional[int] = None,
        status: Optional[str] = None,
        worker_id: Optional[int] = None,
        site_id: Optional[int] = None,
        service_id: Optional[int] = None,
        client_id: Optional[int] = None,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        # Fallback
        loop = asyncio.get_event_loop()
        try:
            if loop.is_running():
                return asyncio.run_coroutine_threadsafe(
                    self._arun(id, status, worker_id, site_id, service_id, client_id),
                    loop,
                ).result()
            else:
                return loop.run_until_complete(
                    self._arun(id, status, worker_id, site_id, service_id, client_id)
                )
        except Exception as e:
            return f"Error in GetAppointmentDetailTool _run: {str(e)}"

    async def _arun(
        self,
        id: Optional[int] = None,
        status: Optional[str] = None,
        worker_id: Optional[int] = None,
        site_id: Optional[int] = None,
        service_id: Optional[int] = None,
        client_id: Optional[int] = None,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        logging.info(
            f"[GetAppointmentDetailTool] _arun called with filters: id={id}, status={status}, worker_id={worker_id}, site_id={site_id}, service_id={service_id}, client_id={client_id}"
        )

        try:
            appointment_details = await business_logic_api.get_appointment_details(
                id=id,
                status=status,
                worker_id=worker_id,
                site_id=site_id,
                service_id=service_id,
                client_id=client_id,
            )

            if appointment_details is None:
                return "No se pudieron obtener los detalles de las citas. La API podría estar caída o la autorización falló."

            if not appointment_details:
                filters_used = []
                if id:
                    filters_used.append(f"ID {id}")
                if status:
                    filters_used.append(f"estado '{status}'")
                if worker_id:
                    filters_used.append(f"trabajador ID {worker_id}")
                if site_id:
                    filters_used.append(f"sitio ID {site_id}")
                if service_id:
                    filters_used.append(f"servicio ID {service_id}")
                if client_id:
                    filters_used.append(f"cliente ID {client_id}")

                filter_text = (
                    " y ".join(filters_used)
                    if filters_used
                    else "los criterios especificados"
                )
                return f"No se encontraron citas que coincidan con {filter_text}."

            # Formatear la respuesta detallada
            return self._format_detailed_appointments_response(appointment_details)

        except Exception as e:
            logging.error(f"[GetAppointmentDetailTool] Error in _arun: {e}")
            return f"Ocurrió un error al intentar obtener los detalles de las citas: {str(e)}"

    def _format_detailed_appointments_response(self, appointments: List[Dict]) -> str:
        """Formatea la respuesta de citas con detalles completos"""
        response_parts = [f"📋 Detalles completos de {len(appointments)} cita(s):"]
        response_parts.append("=" * 50)

        for appointment in appointments:
            # Información básica de la cita
            apt_info = [
                f"🎫 CITA ID {appointment.get('id')}",
                f"🕐 Fecha y hora: {appointment.get('appointmenttime')}",
                f"📋 Estado: {appointment.get('status')}",
                f"👥 Cliente ID: {appointment.get('client_id')}",
                "",
            ]

            # Detalles del trabajador
            worker = appointment.get("worker", {})
            if worker:
                apt_info.extend(
                    [
                        "👤 TRABAJADOR:",
                        f"   Nombre: {worker.get('name', 'N/A')}",
                        f"   ID: {worker.get('id', 'N/A')}",
                        f"   Descripción: {worker.get('description', 'N/A')}",
                        "",
                    ]
                )

            # Detalles del sitio
            site = appointment.get("site", {})
            if site:
                apt_info.extend(
                    [
                        "🏢 SITIO:",
                        f"   Nombre: {site.get('name', 'N/A')}",
                        f"   Dirección: {site.get('address', 'N/A')}",
                        f"   Teléfono: {site.get('phone', 'N/A')}",
                        f"   ID: {site.get('id', 'N/A')}",
                        "",
                    ]
                )

            # Detalles del servicio
            service = appointment.get("service", {})
            if service:
                price = service.get("price")
                price_text = f"${price:,} COP" if price else "N/A"
                duration = service.get("duration")
                duration_text = f"{duration} minutos" if duration else "N/A"

                apt_info.extend(
                    [
                        "💼 SERVICIO:",
                        f"   Nombre: {service.get('name', 'N/A')}",
                        f"   Precio: {price_text}",
                        f"   Duración: {duration_text}",
                        f"   Descripción: {service.get('description', 'N/A')}",
                        f"   ID: {service.get('service_id', 'N/A')}",
                        "",
                    ]
                )

            response_parts.extend(apt_info)
            response_parts.append("-" * 30)
            response_parts.append("")

        return "\n".join(response_parts)
