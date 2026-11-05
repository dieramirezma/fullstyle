import asyncio
import logging
from typing import Any, Dict, List, Optional, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.domain.tools.common import business_logic_api


class GetDetailInput(BaseModel):
    site_id: Optional[int] = Field(
        None,
        description="ID del sitio para filtrar servicios ofrecidos en este sitio específico.",
    )
    service_id: Optional[int] = Field(
        None,
        description="ID del servicio para ver sus detalles en todos los sitios donde se ofrece.",
    )
    name: Optional[str] = Field(
        None,
        description="Nombre o parte del nombre del servicio para búsqueda (ej: 'co' encontrará 'corte simple').",
    )
    price: Optional[int] = Field(
        None,
        description="Precio máximo en pesos colombianos para filtrar servicios hasta este costo.",
    )
    category_id: Optional[int] = Field(
        None, description="ID de la categoría para filtrar servicios de este tipo."
    )
    limit: Optional[int] = Field(
        100, description="Límite máximo de resultados a devolver (por defecto 100)."
    )


class GetDetailTool(BaseTool):
    name: str = "get_details"
    description: str = (
        "Útil para obtener información COMPLETA de servicios ofrecidos en sitios específicos, incluyendo precios, duración y descripciones. "
        "Esta es la tool más completa para consultar servicios ya que incluye nombre del sitio, dirección, categoría, precio en COP, duración en minutos, descripción y fotos. "
        "Puedes filtrar por: sitio específico, tipo de servicio, precio máximo, categoría, o buscar por nombre. "
        "Por ejemplo: buscar 'corte' para encontrar todos los tipos de cortes, o filtrar por precio máximo de 20000 COP para servicios económicos."
    )
    args_schema: Type[BaseModel] = GetDetailInput

    def _run(
        self,
        site_id: Optional[int] = None,
        service_id: Optional[int] = None,
        name: Optional[str] = None,
        price: Optional[int] = None,
        category_id: Optional[int] = None,
        limit: Optional[int] = 100,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        # Fallback
        loop = asyncio.get_event_loop()
        try:
            if loop.is_running():
                return asyncio.run_coroutine_threadsafe(
                    self._arun(
                        site_id=site_id,
                        service_id=service_id,
                        name=name,
                        price=price,
                        category_id=category_id,
                        limit=limit,
                    ),
                    loop,
                ).result()
            else:
                return loop.run_until_complete(
                    self._arun(
                        site_id=site_id,
                        service_id=service_id,
                        name=name,
                        price=price,
                        category_id=category_id,
                        limit=limit,
                    )
                )
        except Exception as e:
            return f"Error in GetDetailTool _run: {str(e)}"

    async def _arun(
        self,
        site_id: Optional[int] = None,
        service_id: Optional[int] = None,
        name: Optional[str] = None,
        price: Optional[int] = None,
        category_id: Optional[int] = None,
        limit: Optional[int] = 100,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        logging.info(
            f"[GetDetailTool] _arun called with filters: site_id={site_id}, service_id={service_id}, name={name}, price={price}, category_id={category_id}, limit={limit}"
        )

        try:
            details = await business_logic_api.get_details(
                site_id=site_id,
                service_id=service_id,
                name=name,
                price=price,
                category_id=category_id,
                limit=limit,
            )

            if details is None:
                return "No se pudieron obtener los detalles de servicios. La API podría estar caída o la autorización falló."

            if not details:
                filters_used = []
                if site_id:
                    filters_used.append(f"sitio ID {site_id}")
                if service_id:
                    filters_used.append(f"servicio ID {service_id}")
                if name:
                    filters_used.append(f"nombre '{name}'")
                if price:
                    filters_used.append(f"precio máximo {price:,} COP")
                if category_id:
                    filters_used.append(f"categoría ID {category_id}")

                filter_text = (
                    " y ".join(filters_used)
                    if filters_used
                    else "los criterios especificados"
                )
                return f"No se encontraron servicios que coincidan con {filter_text}."

            # Formatear la respuesta de manera legible
            return self._format_details_response(details, len(details), limit)

        except Exception as e:
            logging.error(f"[GetDetailTool] Error in _arun: {e}")
            return f"Ocurrió un error al intentar obtener los detalles de servicios: {str(e)}"

    def _format_details_response(
        self, details: List[Dict], total_found: int, limit: int
    ) -> str:
        """Formatea la respuesta de detalles de manera legible para el chatbot"""
        response_parts = []

        # Encabezado con resumen
        if total_found == limit:
            response_parts.append(
                f"Se encontraron {total_found}+ servicios (mostrando primeros {limit}):"
            )
        else:
            response_parts.append(f"Se encontraron {total_found} servicios:")

        response_parts.append("")

        # Agrupar por sitio para mejor organización
        services_by_site = {}
        for detail in details:
            site_key = f"{detail['site_name']} (ID: {detail['site_id']})"
            if site_key not in services_by_site:
                services_by_site[site_key] = []
            services_by_site[site_key].append(detail)

        for site_info, site_services in services_by_site.items():
            response_parts.append(f"🏢 {site_info}")
            response_parts.append(f"   📍 {site_services[0]['site_address']}")
            response_parts.append("")

            for detail in site_services:
                # Información básica del servicio
                service_info = [
                    f"   • {detail['service_name']} (ID: {detail['service_id']})",
                    f"     💰 Precio: ${detail['price']:,} COP",
                    f"     ⏱️ Duración: {detail['duration']} minutos",
                    f"     🏷️ Categoría: {detail['category_name']} (ID: {detail['category_id']})",
                ]

                # Descripción si existe
                if detail.get("description"):
                    service_info.append(f"     📝 Descripción: {detail['description']}")

                # Fotos si existen
                if detail.get("photos") and isinstance(detail["photos"], dict):
                    photos_info = []
                    if detail["photos"].get("before"):
                        photos_info.append("antes")
                    if detail["photos"].get("after"):
                        photos_info.append("después")
                    if photos_info:
                        service_info.append(f"     📸 Fotos: {', '.join(photos_info)}")

                response_parts.extend(service_info)
                response_parts.append("")

        return "\n".join(response_parts)
