import asyncio
import logging
from typing import Any, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.domain.tools.common import business_logic_api


class DeleteAppointmentInput(BaseModel):
    appointment_id: int = Field(
        ..., description="ID de la cita que se quiere cancelar/eliminar."
    )


class DeleteAppointmentTool(BaseTool):
    name: str = "delete_appointment"
    description: str = (
        "Útil para cancelar/eliminar una cita existente. "
        "Solo requiere el ID de la cita que se quiere eliminar. "
        "Una vez eliminada, la cita no se puede recuperar. "
        "Usa get_appointments primero para confirmar que tienes el ID correcto."
    )
    args_schema: Type[BaseModel] = DeleteAppointmentInput

    def _run(self, appointment_id: int, *args: Any, **kwargs: Any) -> str:
        # Fallback
        loop = asyncio.get_event_loop()
        try:
            if loop.is_running():
                return asyncio.run_coroutine_threadsafe(
                    self._arun(appointment_id), loop
                ).result()
            else:
                return loop.run_until_complete(self._arun(appointment_id))
        except Exception as e:
            return f"Error in DeleteAppointmentTool _run: {str(e)}"

    async def _arun(self, appointment_id: int, *args: Any, **kwargs: Any) -> str:
        logging.info(
            f"[DeleteAppointmentTool] _arun called to delete appointment {appointment_id}"
        )

        try:
            result = await business_logic_api.delete_appointment(appointment_id)

            if result is None:
                return f"No se pudo eliminar la cita ID {appointment_id}. La API podría estar caída o hubo un error en la solicitud."

            if isinstance(result, dict) and "error" in result:
                if result.get("status_code") == 404:
                    return f"❌ La cita ID {appointment_id} no fue encontrada. Es posible que ya haya sido eliminada o que el ID sea incorrecto."
                else:
                    return f"No se pudo eliminar la cita ID {appointment_id}. Estado: {result.get('status_code', 'N/A')}. Error: {result.get('error', 'Error desconocido')}"

            # Verificar mensaje de éxito
            if (
                isinstance(result, dict)
                and result.get("message") == "Appointment deleted"
            ):
                return f"✅ Cita ID {appointment_id} eliminada exitosamente."
            elif (
                isinstance(result, dict)
                and result.get("message") == "Appointment not found"
            ):
                return f"❌ La cita ID {appointment_id} no fue encontrada."
            else:
                return f"✅ Cita ID {appointment_id} procesada. Resultado: {result}"

        except Exception as e:
            logging.error(f"[DeleteAppointmentTool] Error in _arun: {e}")
            return f"Ocurrió un error al intentar eliminar la cita ID {appointment_id}: {str(e)}"
