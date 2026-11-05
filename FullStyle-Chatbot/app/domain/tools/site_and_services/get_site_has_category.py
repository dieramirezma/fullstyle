import asyncio
import logging
from typing import Any, Dict, List, Optional, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.domain.tools.common import business_logic_api


class GetSiteHasCategoryInput(BaseModel):
    site_id: Optional[int] = Field(
        None, description="ID del sitio para filtrar qué categorías ofrece este sitio."
    )
    category_id: Optional[int] = Field(
        None,
        description="ID de la categoría para filtrar qué sitios ofrecen esta categoría.",
    )


class GetSiteHasCategoryTool(BaseTool):
    name: str = "get_site_has_category"
    description: str = (
        "Útil para obtener las relaciones entre sitios y categorías de servicios. "
        "Permite identificar qué tipos de servicios ofrece cada sitio o qué sitios ofrecen una categoría específica. "
        "Por ejemplo, puedes averiguar si un sitio es salón de belleza (manicure, maquillaje) o barbería (cortes, afeitado). "
        "Puedes filtrar por ID de sitio para ver todas sus categorías, o por ID de categoría para ver todos los sitios que la ofrecen. "
        "Si recibes nombres en lugar de IDs, usa primero get_sites o get_categories para obtener los IDs correspondientes."
    )
    args_schema: Type[BaseModel] = GetSiteHasCategoryInput

    def _run(
        self,
        site_id: Optional[int] = None,
        category_id: Optional[int] = None,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        # Fallback
        loop = asyncio.get_event_loop()
        try:
            if loop.is_running():
                return asyncio.run_coroutine_threadsafe(
                    self._arun(site_id=site_id, category_id=category_id),
                    loop,
                ).result()
            else:
                return loop.run_until_complete(
                    self._arun(site_id=site_id, category_id=category_id)
                )
        except Exception as e:
            return f"Error in GetSiteHasCategoryTool _run: {str(e)}"

    async def _arun(
        self,
        site_id: Optional[int] = None,
        category_id: Optional[int] = None,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        logging.info(
            f"[GetSiteHasCategoryTool] _arun called with site_id={site_id}, category_id={category_id}"
        )

        try:
            site_categories = await business_logic_api.get_site_has_category(
                site_id=site_id, category_id=category_id
            )

            if site_categories is None:
                return "No se pudieron obtener las relaciones sitio-categoría. La API podría estar caída o la autorización falló."

            if not site_categories:
                filters_used = []
                if site_id:
                    filters_used.append(f"sitio ID {site_id}")
                if category_id:
                    filters_used.append(f"categoría ID {category_id}")

                filter_text = (
                    " y ".join(filters_used) if filters_used else "ningún filtro"
                )
                return (
                    f"No se encontraron relaciones sitio-categoría para {filter_text}."
                )

            # Formatear la respuesta según el contexto
            if site_id and not category_id:
                # Mostrar todas las categorías de un sitio específico
                return self._format_categories_for_site(site_categories, site_id)
            elif category_id and not site_id:
                # Mostrar todos los sitios que ofrecen una categoría específica
                return self._format_sites_for_category(site_categories, category_id)
            else:
                # Vista general o ambos filtros
                return self._format_general_relationships(site_categories)

        except Exception as e:
            logging.error(f"[GetSiteHasCategoryTool] Error in _arun: {e}")
            return f"Ocurrió un error al intentar obtener las relaciones sitio-categoría: {str(e)}"

    def _format_categories_for_site(
        self, site_categories: List[Dict], site_id: int
    ) -> str:
        """Formatea las categorías que ofrece un sitio específico"""
        category_ids = [str(sc["category_id"]) for sc in site_categories]
        categories_text = ", ".join(category_ids)
        return f"El sitio ID {site_id} ofrece las siguientes categorías: {categories_text}. Usa get_categories para obtener los nombres de estas categorías."

    def _format_sites_for_category(
        self, site_categories: List[Dict], category_id: int
    ) -> str:
        """Formatea los sitios que ofrecen una categoría específica"""
        site_ids = [str(sc["site_id"]) for sc in site_categories]
        sites_text = ", ".join(site_ids)
        return f"La categoría ID {category_id} está disponible en los siguientes sitios: {sites_text}. Usa get_sites para obtener los nombres de estos sitios."

    def _format_general_relationships(self, site_categories: List[Dict]) -> str:
        """Formatea una vista general de las relaciones"""
        # Agrupar por sitio para una mejor presentación
        sites_dict = {}
        for sc in site_categories:
            site_id = sc["site_id"]
            category_id = sc["category_id"]

            if site_id not in sites_dict:
                sites_dict[site_id] = []
            sites_dict[site_id].append(category_id)

        response_parts = ["Relaciones sitio-categoría encontradas:"]

        for site_id, category_ids in sites_dict.items():
            categories_str = ", ".join(map(str, category_ids))
            response_parts.append(f"  Sitio ID {site_id}: categorías {categories_str}")

        response_parts.append(
            "\nUsa get_sites y get_categories para obtener los nombres correspondientes a estos IDs."
        )

        return "\n".join(response_parts)
