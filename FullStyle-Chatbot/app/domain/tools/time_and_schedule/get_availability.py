import asyncio
import logging
from typing import Any, Dict, List, Optional, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.domain.tools.common import business_logic_api


class GetAvailabilityInput(BaseModel):
    id: Optional[int] = Field(
        None, description="ID específico de disponibilidad (opcional)."
    )
    worker_id: Optional[int] = Field(
        None, description="ID del trabajador para filtrar su disponibilidad semanal."
    )
    weekday: Optional[str] = Field(
        None,
        description="Día de la semana específico (Lunes, Martes, Miércoles, Jueves, Viernes, Sábado, Domingo).",
    )


class GetAvailabilityTool(BaseTool):
    name: str = "get_availability"
    description: str = (
        "Útil para obtener el horario base/normal de trabajo de los trabajadores por días de la semana. "
        "Este es el horario general que tienen configurado, no la disponibilidad específica de una fecha. "
        "Puedes filtrar por ID de trabajador para ver su horario semanal completo, "
        "o por día específico para ver qué trabajadores trabajan ese día. "
        "Los días se especifican en español: Lunes, Martes, Miércoles, Jueves, Viernes, Sábado, Domingo."
    )
    args_schema: Type[BaseModel] = GetAvailabilityInput

    def _run(
        self,
        id: Optional[int] = None,
        worker_id: Optional[int] = None,
        weekday: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        # Fallback, prefer _arun
        loop = asyncio.get_event_loop()
        try:
            if loop.is_running():
                return asyncio.run_coroutine_threadsafe(
                    self._arun(id=id, worker_id=worker_id, weekday=weekday),
                    loop,
                ).result()
            else:
                return loop.run_until_complete(
                    self._arun(id=id, worker_id=worker_id, weekday=weekday)
                )
        except Exception as e:
            return f"Error in GetAvailabilityTool _run: {str(e)}"

    async def _arun(
        self,
        id: Optional[int] = None,
        worker_id: Optional[int] = None,
        weekday: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        logging.info(
            f"[GetAvailabilityTool] _arun called with id={id}, worker_id={worker_id}, weekday={weekday}"
        )
        try:
            availability_data = await business_logic_api.get_availability(
                id=id, worker_id=worker_id, weekday=weekday
            )

            if availability_data is None:
                return "No se pudo obtener la información de disponibilidad. La API podría estar caída o la autorización falló."

            if not availability_data:
                filters_used = []
                if id:
                    filters_used.append(f"ID {id}")
                if worker_id:
                    filters_used.append(f"trabajador ID {worker_id}")
                if weekday:
                    filters_used.append(f"día {weekday}")

                filter_text = (
                    " y ".join(filters_used)
                    if filters_used
                    else "los criterios especificados"
                )
                return f"No se encontró disponibilidad para {filter_text}."

            # Agrupar por trabajador para mejor presentación
            if worker_id:
                # Si se filtró por trabajador específico, mostrar su horario semanal
                return self._format_worker_schedule(availability_data, worker_id)
            elif weekday:
                # Si se filtró por día específico, mostrar todos los trabajadores ese día
                return self._format_day_schedule(availability_data, weekday)
            else:
                # Vista general
                return self._format_general_schedule(availability_data)

        except Exception as e:
            logging.error(f"[GetAvailabilityTool] Error in _arun: {e}")
            return f"Ocurrió un error al intentar obtener la disponibilidad: {str(e)}"

    def _format_worker_schedule(
        self, availability_data: List[Dict], worker_id: int
    ) -> str:
        """Formatea el horario semanal de un trabajador específico"""
        response_parts = [f"Horario semanal base del trabajador ID {worker_id}:"]

        # Ordenar por día de la semana
        days_order = [
            "Lunes",
            "Martes",
            "Miércoles",
            "Jueves",
            "Viernes",
            "Sábado",
            "Domingo",
        ]
        schedule_by_day = {item["weekday"]: item for item in availability_data}

        working_days = []
        for day in days_order:
            if day in schedule_by_day:
                item = schedule_by_day[day]
                working_days.append(f"  {day}: {item['starttime']} - {item['endtime']}")

        if working_days:
            response_parts.extend(working_days)
        else:
            response_parts.append("  No tiene horarios configurados")

        return "\n".join(response_parts)

    def _format_day_schedule(self, availability_data: List[Dict], weekday: str) -> str:
        """Formatea todos los trabajadores disponibles en un día específico"""
        response_parts = [f"Trabajadores disponibles los {weekday}:"]

        for item in availability_data:
            response_parts.append(
                f"  Trabajador ID {item['worker_id']}: {item['starttime']} - {item['endtime']}"
            )

        return "\n".join(response_parts)

    def _format_general_schedule(self, availability_data: List[Dict]) -> str:
        """Formatea vista general de disponibilidad"""
        # Agrupar por trabajador
        workers_schedule = {}
        for item in availability_data:
            worker_id = item["worker_id"]
            if worker_id not in workers_schedule:
                workers_schedule[worker_id] = []
            workers_schedule[worker_id].append(item)

        response_parts = ["Horarios base configurados:"]

        for worker_id, schedules in workers_schedule.items():
            response_parts.append(f"\nTrabajador ID {worker_id}:")

            # Ordenar por día
            days_order = [
                "Lunes",
                "Martes",
                "Miércoles",
                "Jueves",
                "Viernes",
                "Sábado",
                "Domingo",
            ]
            schedule_by_day = {item["weekday"]: item for item in schedules}

            for day in days_order:
                if day in schedule_by_day:
                    item = schedule_by_day[day]
                    response_parts.append(
                        f"  {day}: {item['starttime']} - {item['endtime']}"
                    )

        return "\n".join(response_parts)
