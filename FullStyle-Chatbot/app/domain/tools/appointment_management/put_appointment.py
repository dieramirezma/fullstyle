import asyncio
import logging
from typing import Any, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.domain.tools.common import business_logic_api


class PutAppointmentInput(BaseModel):
    appointment_id: int = Field(
        ..., description="ID de la cita que se quiere actualizar."
    )
    appointmenttime: str = Field(
        ..., description="Nueva fecha y hora de la cita en formato YYYY-MM-DDTHH:MM:SS."
    )
    status: str = Field(
        ...,
        description="Nuevo estado de la cita (pending, confirmed, canceled, completed).",
    )
    worker_id: int = Field(
        ..., description="ID del trabajador (puede ser el mismo o diferente)."
    )
    site_id: int = Field(
        ..., description="ID del sitio (puede ser el mismo o diferente)."
    )
    service_id: int = Field(
        ..., description="ID del servicio (puede ser el mismo o diferente)."
    )
    client_id: int = Field(
        ..., description="ID del cliente (puede ser el mismo o diferente)."
    )


class PutAppointmentTool(BaseTool):
    name: str = "update_appointment"
    description: str = (
        "Útil para actualizar/modificar una cita existente. "
        "Requiere el ID de la cita a modificar y TODOS los nuevos datos (fecha, estado, trabajador, sitio, servicio, cliente). "
        "IMPORTANTE: Verifica primero que la nueva combinación trabajador-servicio sea válida usando get_worker_has_service. "
        "También verifica disponibilidad con validate_appointment antes de actualizar."
    )
    args_schema: Type[BaseModel] = PutAppointmentInput

    def _run(
        self,
        appointment_id: int,
        appointmenttime: str,
        status: str,
        worker_id: int,
        site_id: int,
        service_id: int,
        client_id: int,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        # Fallback
        loop = asyncio.get_event_loop()
        try:
            if loop.is_running():
                return asyncio.run_coroutine_threadsafe(
                    self._arun(
                        appointment_id,
                        appointmenttime,
                        status,
                        worker_id,
                        site_id,
                        service_id,
                        client_id,
                    ),
                    loop,
                ).result()
            else:
                return loop.run_until_complete(
                    self._arun(
                        appointment_id,
                        appointmenttime,
                        status,
                        worker_id,
                        site_id,
                        service_id,
                        client_id,
                    )
                )
        except Exception as e:
            return f"Error in PutAppointmentTool _run: {str(e)}"

    async def _arun(
        self,
        appointment_id: int,
        appointmenttime: str,
        status: str,
        worker_id: int,
        site_id: int,
        service_id: int,
        client_id: int,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        logging.info(
            f"[PutAppointmentTool] _arun called to update appointment {appointment_id}"
        )

        appointment_data = {
            "appointmenttime": appointmenttime,
            "status": status,
            "worker_id": worker_id,
            "site_id": site_id,
            "service_id": service_id,
            "client_id": client_id,
        }

        try:
            result = await business_logic_api.put_appointment(
                appointment_id, appointment_data
            )

            if result is None:
                return f"No se pudo actualizar la cita ID {appointment_id}. La API podría estar caída o hubo un error en la solicitud."

            if isinstance(result, dict) and "error" in result:
                return f"No se pudo actualizar la cita ID {appointment_id}. Estado: {result.get('status_code', 'N/A')}. Error: {result.get('error', 'Error desconocido')}"

            # Formatear respuesta exitosa
            return f"✅ Cita ID {appointment_id} actualizada exitosamente. Nuevos detalles: {result}"

        except Exception as e:
            logging.error(f"[PutAppointmentTool] Error in _arun: {e}")
            return f"Ocurrió un error al intentar actualizar la cita ID {appointment_id}: {str(e)}"
