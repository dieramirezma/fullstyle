import asyncio
import logging
from typing import Any, Dict, List, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.domain.tools.common import business_logic_api


class GetWorkerDailyScheduleInput(BaseModel):
    worker_id: int = Field(..., description="El ID del trabajador.")
    date: str = Field(
        ...,
        description="La fecha para la cual verificar la disponibilidad, en formato YYYY-MM-DD.",
    )


class GetWorkerDailyScheduleTool(BaseTool):
    name: str = "get_worker_daily_schedule"
    description: str = (
        "Útil para verificar los horarios disponibles para un trabajador específico en una fecha específica. "
        "La entrada requiere el ID del trabajador y la fecha (YYYY-MM-DD)."
    )
    args_schema: Type[BaseModel] = GetWorkerDailyScheduleInput

    def _run(
        self, worker_id: int, date: str, *args: Any, **kwargs: Any
    ) -> List[Dict[str, Any]] | str:
        # Fallback, prefer _arun
        loop = asyncio.get_event_loop()
        try:
            if loop.is_running():
                return asyncio.run_coroutine_threadsafe(
                    business_logic_api.get_worker_daily_schedule(
                        worker_id=worker_id, date=date
                    ),
                    loop,
                ).result()
            else:
                return loop.run_until_complete(
                    business_logic_api.get_worker_daily_schedule(
                        worker_id=worker_id, date=date
                    )
                )
        except Exception as e:
            return f"Error in GetWorkerDailyScheduleTool _run: {str(e)}"

    async def _arun(
        self, worker_id: int, date: str, *args: Any, **kwargs: Any
    ) -> str:  # Return type changed to str
        logging.info(
            f"[GetWorkerDailyScheduleTool] _arun called for worker_id={worker_id}, date={date}"
        )
        try:
            availability_response = await business_logic_api.get_worker_daily_schedule(
                worker_id=worker_id, date=date
            )
            if availability_response is None:
                return f"No se pudo obtener la disponibilidad para el trabajador {worker_id} en la fecha {date}. Problema de API o autenticación, o trabajador/fecha no encontrados."

            schedule = availability_response.get("schedule")
            if not schedule:
                return f"No se encontró información de horario para el trabajador {worker_id} en la fecha {date}."

            available_slots = schedule.get("available", [])
            occupied_slots = schedule.get("occupied", [])

            response_parts = [f"En {date}, para el trabajador ID {worker_id}:"]

            if available_slots:
                available_str = ", ".join(
                    [f"{slot['start']} a {slot['end']}" for slot in available_slots]
                )
                response_parts.append(
                    f"  Horarios generales disponibles: {available_str}."
                )
            else:
                response_parts.append(
                    "  No hay horarios de disponibilidad general listados."
                )

            if occupied_slots:
                occupied_str = ", ".join(
                    [f"{slot['start']} a {slot['end']}" for slot in occupied_slots]
                )
                response_parts.append(
                    f"  Horarios ocupados (citas reservadas): {occupied_str}."
                )
            else:
                response_parts.append("  No hay horarios ocupados listados.")

            if not available_slots and not occupied_slots:
                return f"El trabajador {worker_id} no tiene información de horario (ni horarios disponibles ni ocupados) para {date}. Podría no estar trabajando ese día."

            return "\n".join(response_parts)

        except Exception as e:
            logging.info(f"[GetWorkerDailyScheduleTool] Error in _arun: {e}")
            return f"Ocurrió un error al intentar obtener la disponibilidad: {str(e)}"
