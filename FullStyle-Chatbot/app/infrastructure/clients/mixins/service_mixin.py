import logging
from typing import Any, Dict, List, Optional

import httpx


class ServiceMethodsMixin:
    async def get_services(
        self, name: Optional[str] = None
    ) -> List[Dict[str, Any]] | None:
        """
        Fetches services from the FullStyle Backend API.
        Assumes the endpoint is /api/service.
        Can filter by name.
        """
        if not self.base_url:
            logging.error(
                "Error: BusinessLogicClient cannot fetch services, base_url not configured."
            )
            return None

        params = {}
        if name:
            params["name"] = name

        try:
            url = f"{self.base_url}/service"
            logging.info(
                f"[BusinessLogicClient] Attempting to GET: {url} with params: {params}"
            )
            response = await self.request_with_retry("get", url, params=params)
            services_data = response.json()
            logging.info(
                f"[BusinessLogicClient] Successfully fetched {len(services_data)} services with filter '{name or ''}'."
            )
            return services_data
        except httpx.HTTPStatusError as e:
            logging.error(
                f"[BusinessLogicClient] HTTP error fetching services: {e.response.status_code} - {e.response.text}"
            )
            return None
        except httpx.RequestError as e:
            logging.error(f"[BusinessLogicClient] Request error fetching services: {e}")
            return None
        except Exception as e:
            logging.error(
                f"[BusinessLogicClient] Unexpected error fetching services: {e}"
            )
            return None
