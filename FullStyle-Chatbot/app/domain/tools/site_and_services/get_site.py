import asyncio
import logging
from typing import Any, Optional, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.domain.tools.common import business_logic_api


class GetSiteInput(BaseModel):
    name: Optional[str] = Field(
        None, description="Nombre opcional o parte del nombre para filtrar sitios."
    )
    category_id: Optional[int] = Field(
        None,
        description="ID de categoría opcional para filtrar sitios que ofrecen servicios en esta categoría.",
    )
    service_id: Optional[int] = Field(
        None,
        description="ID de servicio opcional para filtrar sitios que ofrecen este servicio específico.",
    )


class GetSitesTool(BaseTool):
    name: str = "get_sites"
    description: str = (
        "Útil cuando necesitas obtener una lista de todos los sitios (salones/barberías). "
        "Puedes filtrar por nombre, ID de categoría o ID de servicio. "
        "Proporciona ID de sitio, nombre y dirección."
    )
    args_schema: Type[BaseModel] = GetSiteInput

    def _run(
        self,
        name: Optional[str] = None,
        category_id: Optional[int] = None,
        service_id: Optional[int] = None,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        # Fallback
        loop = asyncio.get_event_loop()
        try:
            if loop.is_running():
                return asyncio.run_coroutine_threadsafe(
                    business_logic_api.get_sites(
                        name=name, category_id=category_id, service_id=service_id
                    ),
                    loop,
                ).result()
            else:
                return loop.run_until_complete(
                    business_logic_api.get_sites(
                        name=name, category_id=category_id, service_id=service_id
                    )
                )
        except Exception as e:
            return f"Error in GetSitesTool _run: {str(e)}"

    async def _arun(
        self,
        name: Optional[str] = None,
        category_id: Optional[int] = None,
        service_id: Optional[int] = None,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        logging.info(
            f"[GetSitesTool] _arun called with filters: name='{name}', category_id={category_id}, service_id={service_id}"
        )
        try:
            sites = await business_logic_api.get_sites(
                name=name, category_id=category_id, service_id=service_id
            )
            if sites is None:
                return "No se pudieron obtener los sitios. La API podría estar caída o la autorización falló."
            if not sites:
                return "No se encontraron sitios que coincidan con tus criterios."

            formatted_sites = []
            for site in sites:
                site_id = site.get("id", "N/A")
                site_name = site.get("name", "N/A")
                site_address = site.get("address", "N/A")
                formatted_sites.append(
                    f"ID: {site_id}, Nombre: {site_name}, Dirección: {site_address}"
                )

            return "Lista de sitios: " + "; ".join(formatted_sites)
        except Exception as e:
            logging.info(f"[GetSitesTool] Error in _arun: {e}")
            return f"Ocurrió un error al intentar obtener los sitios: {str(e)}"
