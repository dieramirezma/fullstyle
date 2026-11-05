import logging
from typing import Any, Dict, List, Optional

import httpx


class SiteMethodsMixin:
    async def get_sites(
        self,
        name: Optional[str] = None,
        category_id: Optional[int] = None,
        service_id: Optional[int] = None,
    ) -> List[Dict[str, Any]] | None:
        """
        Fetches sites from the FullStyle Backend API.
        Can filter by name, category_id, and service_id.
        """
        if not self.base_url:
            logging.error(
                "Error: BusinessLogicClient cannot fetch sites, base_url not configured."
            )
            return None

        params = {}
        if name:
            params["name"] = name
        if category_id is not None:
            params["category_id"] = category_id
        if service_id is not None:
            params["service_id"] = service_id

        try:
            url = f"{self.base_url}/site"
            logging.info(
                f"[BusinessLogicClient] Attempting to GET: {url} with params: {params}"
            )
            response = await self.request_with_retry("get", url, params=params)
            sites_data = response.json()
            logging.info(
                f"[BusinessLogicClient] Successfully fetched {len(sites_data)} sites."
            )
            return sites_data
        except httpx.HTTPStatusError as e:
            logging.error(
                f"[BusinessLogicClient] HTTP error fetching sites: {e.response.status_code} - {e.response.text}"
            )
            return None
        except httpx.RequestError as e:
            logging.error(f"[BusinessLogicClient] Request error fetching sites: {e}")
            return None
        except Exception as e:
            logging.error(f"[BusinessLogicClient] Unexpected error fetching sites: {e}")
            return None
