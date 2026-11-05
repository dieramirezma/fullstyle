import asyncio
import logging
from typing import Any, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.domain.tools.common import business_logic_api


class ValidateAppointmentInput(BaseModel):
    client_id: int = Field(..., description="El ID del cliente que quiere agendar.")
    worker_id: int = Field(..., description="El ID del trabajador para la validación.")
    service_id: int = Field(..., description="El ID del servicio para la validación.")
    site_id: int = Field(
        ..., description="El ID del sitio donde se realizaría la cita."
    )
    appointment_time: str = Field(
        ...,
        description="La fecha y hora de inicio propuesta en formato YYYY-MM-DDTHH:MM:SS.",
    )


class ValidateAppointmentTool(BaseTool):
    name: str = "validate_appointment"
    description: str = (
        "Útil para verificar si una cita se puede agendar en un horario específico SIN crearla realmente. "
        "Verifica disponibilidad del trabajador, solapamientos con otras citas, días libres, y horarios de trabajo. "
        "Perfecto para confirmar disponibilidad antes de proceder con la reserva."
    )
    args_schema: Type[BaseModel] = ValidateAppointmentInput

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
            return f"Error in ValidateAppointmentTool _run: {str(e)}"

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
            f"[ValidateAppointmentTool] _arun called to validate appointment: client={client_id}, worker={worker_id}, service={service_id}, site={site_id}, time={appointment_time}"
        )

        validation_data = {
            "client_id": client_id,
            "worker_id": worker_id,
            "service_id": service_id,
            "site_id": site_id,
            "appointmenttime": appointment_time,
            "status": "pending",
            "request": True,  # Always validate only
        }

        try:
            result = await business_logic_api.post_appointment(validation_data)

            if result is None:
                return "No se pudo validar la reserva. La API podría estar caída o hubo un error en la solicitud."

            if isinstance(result, dict) and "error" in result:
                return f"No se pudo validar la reserva. Estado: {result.get('status_code', 'N/A')}. Error: {result.get('error', 'Error desconocido')}"

            # Handle validation response
            if isinstance(result, dict) and "validation_result" in result:
                validation_result = result["validation_result"]
                if validation_result is True:
                    return "✅ La cita SÍ se puede agendar en este horario. El trabajador está disponible."
                elif (
                    isinstance(validation_result, dict)
                    and "message" in validation_result
                ):
                    return (
                        f"❌ La cita NO se puede agendar: {validation_result['message']}"
                    )
                else:
                    return f"❌ La cita NO se puede agendar: {validation_result}"
            else:
                # Direct response from backend
                if result is True:
                    return "✅ La cita SÍ se puede agendar en este horario. El trabajador está disponible."
                elif isinstance(result, dict) and "message" in result:
                    return f"❌ La cita NO se puede agendar: {result['message']}"
                else:
                    return f"❌ La cita NO se puede agendar: {result}"

        except Exception as e:
            logging.error(f"[ValidateAppointmentTool] Error in _arun: {e}")
            return f"Ocurrió un error al intentar validar la reserva: {str(e)}"
