import asyncio
import logging
from typing import Any, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.domain.tools.common import business_logic_api


class PostAppointmentInput(BaseModel):
    client_id: int = Field(..., description="El ID del cliente que realiza la reserva.")
    worker_id: int = Field(..., description="El ID del trabajador para la reserva.")
    service_id: int = Field(..., description="El ID del servicio para la reserva.")
    site_id: int = Field(
        ..., description="El ID del sitio donde se realiza la reserva."
    )
    appointment_time: str = Field(
        ...,
        description="La fecha y hora de inicio de la cita en formato YYYY-MM-DD HH:MM:SS.",
    )


class PostAppointmentTool(BaseTool):
    name: str = "post_appointment"
    description: str = (
        "Útil para crear una nueva cita o reserva. "
        "Requiere ID de cliente, ID de trabajador, ID de servicio, ID de sitio, y hora de inicio de la cita (YYYY-MM-DD HH:MM:SS)."
        "IMPORTANTE: Usar validate_appointment primero para verificar que si se pueda agendar la cita sin conflictos de disponibilidad."
    )
    args_schema: Type[BaseModel] = PostAppointmentInput

    def _run(
        self,
        client_id: int,
        worker_id: int,
        service_id: int,
        site_id: int,
        appointment_time: str,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        # Fallback
        loop = asyncio.get_event_loop()
        try:
            if loop.is_running():
                return asyncio.run_coroutine_threadsafe(
                    self._arun(
                        client_id, worker_id, service_id, site_id, appointment_time
                    ),
                    loop,
                ).result()
            else:
                return loop.run_until_complete(
                    self._arun(
                        client_id, worker_id, service_id, site_id, appointment_time
                    )
                )
        except Exception as e:
            return f"Error in PostAppointmentTool _run: {str(e)}"

    async def _arun(
        self,
        client_id: int,
        worker_id: int,
        service_id: int,
        site_id: int,
        appointment_time: str,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        logging.info(
            f"[PostAppointmentTool] _arun called to create appointment: client={client_id}, worker={worker_id}, service={service_id}, site={site_id}, time={appointment_time}"
        )

        reservation_data = {
            "client_id": client_id,
            "worker_id": worker_id,
            "service_id": service_id,
            "site_id": site_id,
            "appointmenttime": appointment_time,
            "status": "pending",
            "request": False,  # Always create, never just validate
        }

        try:
            result = await business_logic_api.post_appointment(reservation_data)

            if result is None:
                return "No se pudo crear la reserva. La API podría estar caída o hubo un error en la solicitud."

            if isinstance(result, dict) and "error" in result:
                return f"No se pudo crear la reserva. Estado: {result.get('status_code', 'N/A')}. Error: {result.get('error', 'Error desconocido')}"

            # Handle creation response
            if isinstance(result, dict) and "id" in result:
                return f"✅ Reserva creada exitosamente. ID de la cita: {result['id']}. Detalles: {result}"
            else:
                return f"✅ Reserva creada exitosamente. Detalles: {result}"

        except Exception as e:
            logging.error(f"[PostAppointmentTool] Error in _arun: {e}")
            return f"Ocurrió un error al intentar crear la reserva: {str(e)}"
