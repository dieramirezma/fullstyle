import asyncio
import logging
from typing import Any, Dict, List, Optional, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.domain.tools.common import business_logic_api


class GetAppointmentInput(BaseModel):
    id: Optional[int] = Field(
        None, description="ID específico de la cita para obtener una cita particular."
    )
    status: Optional[str] = Field(
        None,
        description="Estado de la cita para filtrar (pending, confirmed, canceled, completed).",
    )
    worker_id: Optional[int] = Field(
        None, description="ID del trabajador para ver todas sus citas."
    )
    site_id: Optional[int] = Field(
        None, description="ID del sitio para ver todas las citas de este lugar."
    )
    service_id: Optional[int] = Field(
        None,
        description="ID del servicio para ver todas las citas de este tipo de servicio.",
    )
    client_id: Optional[int] = Field(
        None, description="ID del cliente para ver todas sus citas."
    )


class GetAppointmentTool(BaseTool):
    name: str = "get_appointments"
    description: str = (
        "Útil para obtener información básica de citas existentes. "
        "Puedes filtrar por ID específico, estado (pending/confirmed/canceled/completed), "
        "trabajador, sitio, servicio o cliente. "
        "Devuelve información básica como ID, fecha/hora, estado e IDs relacionados. "
        "Para información detallada con nombres y descripciones, usa get_appointment_details."
    )
    args_schema: Type[BaseModel] = GetAppointmentInput

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
            return f"Error in GetAppointmentTool _run: {str(e)}"

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
            f"[GetAppointmentTool] _arun called with filters: id={id}, status={status}, worker_id={worker_id}, site_id={site_id}, service_id={service_id}, client_id={client_id}"
        )

        try:
            appointments = await business_logic_api.get_appointments(
                id=id,
                status=status,
                worker_id=worker_id,
                site_id=site_id,
                service_id=service_id,
                client_id=client_id,
            )

            if appointments is None:
                return "No se pudieron obtener las citas. La API podría estar caída o la autorización falló."

            if not appointments:
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

            # Formatear la respuesta
            return self._format_appointments_response(appointments)

        except Exception as e:
            logging.error(f"[GetAppointmentTool] Error in _arun: {e}")
            return f"Ocurrió un error al intentar obtener las citas: {str(e)}"

    def _format_appointments_response(self, appointments: List[Dict]) -> str:
        """Formatea la respuesta de citas básicas"""
        response_parts = [f"Se encontraron {len(appointments)} citas:"]
        response_parts.append("")

        for appointment in appointments:
            apt_info = [
                f"📅 Cita ID {appointment.get('id')}:",
                f"  🕐 Fecha y hora: {appointment.get('appointmenttime')}",
                f"  📋 Estado: {appointment.get('status')}",
                f"  👤 Trabajador ID: {appointment.get('worker_id')}",
                f"  🏢 Sitio ID: {appointment.get('site_id')}",
                f"  💼 Servicio ID: {appointment.get('service_id')}",
                f"  👥 Cliente ID: {appointment.get('client_id')}",
                "",
            ]
            response_parts.extend(apt_info)

        response_parts.append(
            "💡 Para obtener información detallada (nombres, descripciones, precios), usa get_appointment_details."
        )

        return "\n".join(response_parts)
