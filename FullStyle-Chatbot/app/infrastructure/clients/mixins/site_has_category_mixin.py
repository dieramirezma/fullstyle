import logging
from typing import Any, Dict, List, Optional

import httpx


class SiteHasCategoryMethodsMixin:
    async def get_site_has_category(
        self,
        site_id: Optional[int] = None,
        category_id: Optional[int] = None,
    ) -> List[Dict[str, Any]] | None:
        """
        Fetches site-category relationships from the FullStyle Backend API.
        Can filter by site_id, category_id, or both.
        """
        if not self.base_url:
            logging.error(
                "Error: BusinessLogicClient cannot fetch site-category relationships, base_url not configured."
            )
            return None

        params = {}
        if site_id is not None:
            params["site_id"] = site_id
        if category_id is not None:
            params["category_id"] = category_id

        try:
            url = f"{self.base_url}/site_has_category"
            logging.info(
                f"[BusinessLogicClient] Attempting to GET: {url} with params: {params}"
            )
            response = await self.request_with_retry("get", url, params=params)
            site_categories_data = response.json()
            logging.info(
                f"[BusinessLogicClient] Successfully fetched {len(site_categories_data)} site-category relationships."
            )
            return site_categories_data
        except httpx.HTTPStatusError as e:
            logging.error(
                f"[BusinessLogicClient] HTTP error fetching site-category relationships: {e.response.status_code} - {e.response.text}"
            )
            return None
        except httpx.RequestError as e:
            logging.error(
                f"[BusinessLogicClient] Request error fetching site-category relationships: {e}"
            )
            return None
        except Exception as e:
            logging.error(
                f"[BusinessLogicClient] Unexpected error fetching site-category relationships: {e}"
            )
            return None
