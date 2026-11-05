import logging
from typing import Any, Dict, List

import httpx


class CategoryMethodsMixin:
    async def get_categories(self) -> List[Dict[str, Any]] | None:
        """
        Fetches all categories from the FullStyle Backend API.
        No parameters required - returns all categories.
        """
        if not self.base_url:
            logging.error(
                "Error: BusinessLogicClient cannot fetch categories, base_url not configured."
            )
            return None

        try:
            url = f"{self.base_url}/category"
            logging.info(f"[BusinessLogicClient] Attempting to GET: {url}")
            response = await self.request_with_retry("get", url)
            categories_data = response.json()
            logging.info(
                f"[BusinessLogicClient] Successfully fetched {len(categories_data)} categories."
            )
            return categories_data
        except httpx.HTTPStatusError as e:
            logging.error(
                f"[BusinessLogicClient] HTTP error fetching categories: {e.response.status_code} - {e.response.text}"
            )
            return None
        except httpx.RequestError as e:
            logging.error(
                f"[BusinessLogicClient] Request error fetching categories: {e}"
            )
            return None
        except Exception as e:
            logging.error(
                f"[BusinessLogicClient] Unexpected error fetching categories: {e}"
            )
            return None
