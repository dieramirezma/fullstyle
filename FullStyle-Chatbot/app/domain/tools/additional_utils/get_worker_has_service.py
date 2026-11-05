import asyncio
import logging
from typing import Any, Dict, List, Optional, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.domain.tools.common import business_logic_api


class GetWorkerHasServiceInput(BaseModel):
    worker_id: Optional[int] = Field(
        None, description="ID del trabajador para ver qué servicios puede realizar."
    )
    service_id: Optional[int] = Field(
        None, description="ID del servicio para ver qué trabajadores pueden realizarlo."
    )


class GetWorkerHasServiceTool(BaseTool):
    name: str = "get_worker_has_service"
    description: str = (
        "Útil para obtener las relaciones entre trabajadores y servicios que pueden realizar. "
        "CRÍTICO para verificar compatibilidad antes de agendar citas - un trabajador solo puede realizar servicios que tenga asignados. "
        "Puedes filtrar por ID de trabajador para ver todos sus servicios, o por ID de servicio para ver quién puede realizarlo. "
        "Si recibes nombres en lugar de IDs, usa primero get_workers para obtener worker_id y get_services para obtener service_id. "
        "Esta verificación es OBLIGATORIA antes de usar post_appointment."
    )
    args_schema: Type[BaseModel] = GetWorkerHasServiceInput

    def _run(
        self,
        worker_id: Optional[int] = None,
        service_id: Optional[int] = None,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        # Fallback
        loop = asyncio.get_event_loop()
        try:
            if loop.is_running():
                return asyncio.run_coroutine_threadsafe(
                    self._arun(worker_id=worker_id, service_id=service_id),
                    loop,
                ).result()
            else:
                return loop.run_until_complete(
                    self._arun(worker_id=worker_id, service_id=service_id)
                )
        except Exception as e:
            return f"Error in GetWorkerHasServiceTool _run: {str(e)}"

    async def _arun(
        self,
        worker_id: Optional[int] = None,
        service_id: Optional[int] = None,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        logging.info(
            f"[GetWorkerHasServiceTool] _arun called with worker_id={worker_id}, service_id={service_id}"
        )

        try:
            worker_services = await business_logic_api.get_worker_has_service(
                worker_id=worker_id, service_id=service_id
            )

            if worker_services is None:
                return "No se pudieron obtener las relaciones trabajador-servicio. La API podría estar caída o la autorización falló."

            if not worker_services:
                filters_used = []
                if worker_id:
                    filters_used.append(f"trabajador ID {worker_id}")
                if service_id:
                    filters_used.append(f"servicio ID {service_id}")

                filter_text = (
                    " y ".join(filters_used) if filters_used else "ningún filtro"
                )
                return f"No se encontraron relaciones trabajador-servicio para {filter_text}."

            # Formatear la respuesta según el contexto
            if worker_id and not service_id:
                # Mostrar todos los servicios que puede realizar un trabajador específico
                return self._format_services_for_worker(worker_services, worker_id)
            elif service_id and not worker_id:
                # Mostrar todos los trabajadores que pueden realizar un servicio específico
                return self._format_workers_for_service(worker_services, service_id)
            else:
                # Vista general o ambos filtros
                return self._format_general_relationships(worker_services)

        except Exception as e:
            logging.error(f"[GetWorkerHasServiceTool] Error in _arun: {e}")
            return f"Ocurrió un error al intentar obtener las relaciones trabajador-servicio: {str(e)}"

    def _format_services_for_worker(
        self, worker_services: List[Dict], worker_id: int
    ) -> str:
        """Formatea los servicios que puede realizar un trabajador específico"""
        service_ids = [str(ws["service_id"]) for ws in worker_services]
        services_text = ", ".join(service_ids)

        return (
            f"El trabajador ID {worker_id} puede realizar los siguientes servicios: {services_text}. "
            f"Usa get_services para obtener los nombres de estos servicios. "
            f"IMPORTANTE: Solo puede agendar citas con estos service_ids."
        )

    def _format_workers_for_service(
        self, worker_services: List[Dict], service_id: int
    ) -> str:
        """Formatea los trabajadores que pueden realizar un servicio específico"""
        worker_ids = [str(ws["worker_id"]) for ws in worker_services]
        workers_text = ", ".join(worker_ids)

        return (
            f"El servicio ID {service_id} puede ser realizado por los siguientes trabajadores: {workers_text}. "
            f"Usa get_workers para obtener los nombres de estos trabajadores. "
            f"IMPORTANTE: Solo estos worker_ids pueden realizar este servicio."
        )

    def _format_general_relationships(self, worker_services: List[Dict]) -> str:
        """Formatea una vista general de las relaciones"""
        # Agrupar por trabajador para una mejor presentación
        workers_dict = {}
        for ws in worker_services:
            worker_id = ws["worker_id"]
            service_id = ws["service_id"]

            if worker_id not in workers_dict:
                workers_dict[worker_id] = []
            workers_dict[worker_id].append(service_id)

        response_parts = ["Relaciones trabajador-servicio encontradas:"]

        for worker_id, service_ids in workers_dict.items():
            services_str = ", ".join(map(str, service_ids))
            response_parts.append(
                f"  Trabajador ID {worker_id}: servicios {services_str}"
            )

        response_parts.extend(
            [
                "",
                "Usa get_workers y get_services para obtener los nombres correspondientes a estos IDs.",
                "RECORDATORIO: Estas relaciones son obligatorias para validar antes de agendar citas.",
            ]
        )

        return "\n".join(response_parts)
