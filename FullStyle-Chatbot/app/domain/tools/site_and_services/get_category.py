import asyncio
import logging
from typing import Any, Type

from langchain.tools import BaseTool
from pydantic import BaseModel

from app.domain.tools.common import business_logic_api


class GetCategoryInput(BaseModel):
    # No requiere parámetros
    pass


class GetCategoryTool(BaseTool):
    name: str = "get_categories"
    description: str = (
        "Útil para obtener todas las categorías generales de servicios disponibles. "
        "Las categorías incluyen tipos como Corte de Cabello, Coloración, Tratamientos Capilares, "
        "Tratamientos Faciales, Barbería, Manicure y Pedicure, Depilación, etc. "
        "No requiere parámetros de entrada."
    )
    args_schema: Type[BaseModel] = GetCategoryInput

    def _run(self, *args: Any, **kwargs: Any) -> str:
        # Fallback
        loop = asyncio.get_event_loop()
        try:
            if loop.is_running():
                return asyncio.run_coroutine_threadsafe(
                    business_logic_api.get_categories(), loop
                ).result()
            else:
                return loop.run_until_complete(business_logic_api.get_categories())
        except Exception as e:
            return f"Error in GetCategoryTool _run: {str(e)}"

    async def _arun(self, *args: Any, **kwargs: Any) -> str:
        logging.info("[GetCategoryTool] _arun called to fetch all categories")

        try:
            categories = await business_logic_api.get_categories()

            if categories is None:
                return "No se pudieron obtener las categorías. La API podría estar caída o la autorización falló."

            if not categories:
                return "No se encontraron categorías disponibles."

            # Formatear las categorías para el chatbot
            formatted_categories = []
            for category in categories:
                category_id = category.get("id", "N/A")
                category_name = category.get("name", "N/A")
                formatted_categories.append(f"ID {category_id}: {category_name}")

            categories_text = "; ".join(formatted_categories)
            return f"Categorías de servicios disponibles: {categories_text}"

        except Exception as e:
            logging.error(f"[GetCategoryTool] Error in _arun: {e}")
            return f"Ocurrió un error al intentar obtener las categorías: {str(e)}"
