import logging
from typing import Any, Dict, List, Optional

import httpx


class AvailabilityMethodsMixin:
    async def get_availability(
        self,
        id: Optional[int] = None,
        worker_id: Optional[int] = None,
        weekday: Optional[str] = None,
    ) -> List[Dict[str, Any]] | None:
        """
        Fetches availability from the FullStyle Backend API.
        Can filter by id, worker_id, and weekday.
        """
        if not self.base_url:
            logging.error(
                "Error: BusinessLogicClient cannot fetch availability, base_url not configured."
            )
            return None

        params = {}
        if id is not None:
            params["id"] = id
        if worker_id is not None:
            params["worker_id"] = worker_id
        if weekday:
            params["weekday"] = weekday

        try:
            url = f"{self.base_url}/availability"
            logging.info(
                f"[BusinessLogicClient] Attempting to GET: {url} with params: {params}"
            )
            response = await self.request_with_retry("get", url, params=params)
            availability_data = response.json()
            logging.info(
                f"[BusinessLogicClient] Successfully fetched {len(availability_data)} availability records."
            )
            return availability_data
        except httpx.HTTPStatusError as e:
            logging.error(
                f"[BusinessLogicClient] HTTP error fetching availability: {e.response.status_code} - {e.response.text}"
            )
            return None
        except httpx.RequestError as e:
            logging.error(
                f"[BusinessLogicClient] Request error fetching availability: {e}"
            )
            return None
        except Exception as e:
            logging.error(
                f"[BusinessLogicClient] Unexpected error fetching availability: {e}"
            )
            return None
