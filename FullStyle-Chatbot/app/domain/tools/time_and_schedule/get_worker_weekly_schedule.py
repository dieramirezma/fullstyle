import asyncio
import logging
from typing import Any, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.domain.tools.common import business_logic_api


class GetWorkerWeeklyScheduleInput(BaseModel):
    worker_id: int = Field(..., description="El ID del trabajador.")
    date: str = Field(
        ...,
        description="La fecha de referencia para la semana, en formato YYYY-MM-DD. Se calculará la semana completa que contiene esta fecha.",
    )


class GetWorkerWeeklyScheduleTool(BaseTool):
    name: str = "get_worker_weekly_schedule"
    description: str = (
        "Útil para verificar los horarios disponibles para un trabajador específico durante toda una semana. "
        "La entrada requiere el ID del trabajador y una fecha de referencia (YYYY-MM-DD) para determinar qué semana consultar. "
        "Devuelve el horario completo de lunes a domingo."
    )
    args_schema: Type[BaseModel] = GetWorkerWeeklyScheduleInput

    def _run(self, worker_id: int, date: str, *args: Any, **kwargs: Any) -> str:
        # Fallback, prefer _arun
        loop = asyncio.get_event_loop()
        try:
            if loop.is_running():
                return asyncio.run_coroutine_threadsafe(
                    business_logic_api.get_worker_weekly_schedule(
                        worker_id=worker_id, date=date
                    ),
                    loop,
                ).result()
            else:
                return loop.run_until_complete(
                    business_logic_api.get_worker_weekly_schedule(
                        worker_id=worker_id, date=date
                    )
                )
        except Exception as e:
            return f"Error in GetWorkerWeeklyScheduleTool _run: {str(e)}"

    async def _arun(self, worker_id: int, date: str, *args: Any, **kwargs: Any) -> str:
        logging.info(
            f"[GetWorkerWeeklyScheduleTool] _arun called for worker_id={worker_id}, date={date}"
        )
        try:
            weekly_response = await business_logic_api.get_worker_weekly_schedule(
                worker_id=worker_id, date=date
            )
            if weekly_response is None:
                return f"No se pudo obtener el horario semanal para el trabajador {worker_id} en la semana que contiene {date}. Problema de API o autenticación, o trabajador/fecha no encontrados."

            schedule = weekly_response.get("schedule")
            week_start = weekly_response.get("week_start")
            week_end = weekly_response.get("week_end")

            if not schedule:
                return f"No se encontró información de horario semanal para el trabajador {worker_id} en la semana del {week_start} al {week_end}."

            response_parts = [
                f"Horario semanal para el trabajador ID {worker_id}",
                f"Semana del {week_start} al {week_end}:",
                "",
            ]

            # Días en orden
            days_order = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
            days_es = {
                "Monday": "Lunes",
                "Tuesday": "Martes",
                "Wednesday": "Miércoles",
                "Thursday": "Jueves",
                "Friday": "Viernes",
                "Saturday": "Sábado",
                "Sunday": "Domingo",
            }

            for day_en in days_order:
                if day_en in schedule:
                    day_schedule = schedule[day_en]
                    day_es = days_es[day_en]

                    available_slots = day_schedule.get("available", [])
                    occupied_slots = day_schedule.get("occupied", [])

                    if not available_slots and not occupied_slots:
                        response_parts.append(f"  {day_es}: No está trabajando")
                    else:
                        day_info = [f"  {day_es}:"]

                        if available_slots:
                            available_str = ", ".join(
                                [
                                    f"{slot['start']}-{slot['end']}"
                                    for slot in available_slots
                                ]
                            )
                            day_info.append(f"    Disponible: {available_str}")

                        if occupied_slots:
                            occupied_str = ", ".join(
                                [
                                    f"{slot['start']}-{slot['end']}"
                                    for slot in occupied_slots
                                ]
                            )
                            day_info.append(f"    Ocupado: {occupied_str}")

                        response_parts.append("\n".join(day_info))

            return "\n".join(response_parts)

        except Exception as e:
            logging.info(f"[GetWorkerWeeklyScheduleTool] Error in _arun: {e}")
            return f"Ocurrió un error al intentar obtener el horario semanal: {str(e)}"
