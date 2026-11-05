import asyncio
import logging
from typing import Any, Dict, List, Optional, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.domain.tools.common import business_logic_api


class GetServiceInput(BaseModel):
    name: Optional[str] = Field(
        None,
        description="Nombre opcional o parte del nombre para filtrar servicios (ej: 'corte', 'color').",
    )


class GetServicesTool(BaseTool):
    name: str = "get_services"
    description: str = (
        "Útil cuando necesitas obtener una lista de todos los servicios disponibles. "
        "Opcionalmente puedes filtrar por nombre de servicio (ej: para encontrar todos los tipos de 'cortes de pelo'). "
        "Proporciona ID de servicio, nombre y ID de categoría."
    )
    args_schema: Type[BaseModel] = GetServiceInput

    def _run(
        self, name: Optional[str] = None, *args: Any, **kwargs: Any
    ) -> List[Dict[str, Any]] | str:
        # Fallback
        loop = asyncio.get_event_loop()
        try:
            if loop.is_running():
                return asyncio.run_coroutine_threadsafe(
                    business_logic_api.get_services(name=name), loop
                ).result()
            else:
                return loop.run_until_complete(
                    business_logic_api.get_services(name=name)
                )
        except Exception as e:
            return f"Error in GetServicesTool _run: {str(e)}"

    async def _arun(self, name: Optional[str] = None, *args: Any, **kwargs: Any) -> str:
        logging.info(f"[GetServicesTool] _arun called with name filter: '{name}'")
        try:
            services = await business_logic_api.get_services(name=name)
            if services is None:
                return "No se pudieron obtener los servicios. La API podría estar caída o la autorización falló."
            if not services:
                return f"No se encontraron servicios que coincidan con el filtro {name or ''}."

            formatted_services = []
            for service in services:
                service_id = service.get("id", "N/A")
                service_name = service.get("name", "N/A")
                category_id = service.get("category_id", "N/A")
                formatted_services.append(
                    f"ID: {service_id}, Nombre: {service_name}, ID Categoría: {category_id}"
                )

            return "Lista de servicios: " + "; ".join(formatted_services)
        except Exception as e:
            logging.info(f"[GetServicesTool] Error in _arun: {e}")
            return f"Ocurrió un error al intentar obtener los servicios: {str(e)}"
