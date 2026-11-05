import asyncio
import logging
from typing import Any, Dict, List, Optional, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.domain.tools.common import business_logic_api


class GetWorkerInput(BaseModel):
    site_id: Optional[int] = Field(
        None, description="ID opcional del sitio para filtrar trabajadores."
    )
    name: Optional[str] = Field(
        None,
        description="Nombre opcional o parte del nombre para filtrar trabajadores.",
    )
    service_id: Optional[int] = Field(
        None,
        description="ID opcional del servicio para filtrar trabajadores que puedan realizarlo.",
    )


class GetWorkersTool(BaseTool):
    name: str = "get_workers"
    description: str = (
        "Útil cuando necesitas obtener una lista de trabajadores o miembros del personal disponibles. "
        "Puedes filtrar por ID de sitio, nombre del trabajador o ID de servicio. "
        "Por ejemplo, para encontrar barberos en el sitio 1, o encontrar estilistas que puedan hacer coloración."
    )
    args_schema: Type[BaseModel] = GetWorkerInput

    def _run(self, *args: Any, **kwargs: Any) -> List[Dict[str, Any]] | str:
        loop = asyncio.get_event_loop()
        try:
            # Check if an event loop is already running. If so, use it. Otherwise, run a new one
            if loop.is_running():
                return asyncio.run_coroutine_threadsafe(
                    business_logic_api.get_workers(), loop
                ).result()

            else:
                return loop.run_until_complete(business_logic_api.get_workers())
        except Exception as e:
            return f"Error in GetWorkersTool _run: {str(e)}"

    async def _arun(
        self,
        site_id: Optional[int] = None,
        name: Optional[str] = None,
        service_id: Optional[int] = None,
    ) -> List[Dict[str, Any]] | str:
        """Usa esta herramienta para obtener una lista de todos los trabajadores, opcionalmente filtrando por sitio, nombre o servicio."""
        logging.info(
            f"[GetWorkersTool] _arun called with site_id={site_id}, name={name}, service_id={service_id}"
        )
        try:
            workers = await business_logic_api.get_workers(
                site_id=site_id, name=name, service_id=service_id
            )
            if workers is None:
                return "No se pudieron obtener los trabajadores. La API podría estar caída, el endpoint podría ser incorrecto o la autorización falló."
            if not workers:
                return "No se encontraron trabajadores que coincidan con tus criterios."

            formatted_workers = []
            for worker in workers:
                # Use 'id' as the 'id_worker'
                worker_id = worker.get("id", "N/A")
                worker_name = worker.get("name", "N/A")
                description = worker.get("description", "N/A")
                active = worker.get("active", False)
                if active:
                    formatted_workers.append(
                        f"ID: {worker_id}, Nombre: {worker_name}, Descripción: {description}"
                    )

            if not formatted_workers:
                return "No se encontraron trabajadores activos que coincidan con tus criterios o los datos de los trabajadores no están en el formato esperado."

            return "Lista de trabajadores activos: " + "; ".join(formatted_workers)

        except Exception as e:
            logging.info(f"[GetWorkersTool] Error in _arun: {e}")
            return f"Ocurrió un error al intentar obtener los trabajadores: {str(e)}"
