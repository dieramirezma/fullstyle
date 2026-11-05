import logging
from typing import Any, Dict, List, Optional

import httpx


class DetailMethodsMixin:
    async def get_details(
        self,
        site_id: Optional[int] = None,
        service_id: Optional[int] = None,
        name: Optional[str] = None,
        price: Optional[int] = None,
        category_id: Optional[int] = None,
        limit: Optional[int] = 100,
    ) -> List[Dict[str, Any]] | None:
        """
        Fetches service details from the FullStyle Backend API.
        Can filter by site_id, service_id, name (partial match), price (max), category_id, and limit results.
        """
        if not self.base_url:
            logging.error(
                "Error: BusinessLogicClient cannot fetch service details, base_url not configured."
            )
            return None

        params = {}
        if site_id is not None:
            params["site_id"] = site_id
        if service_id is not None:
            params["service_id"] = service_id
        if name:
            params["name"] = name
        if price is not None:
            params["price"] = price
        if category_id is not None:
            params["category_id"] = category_id
        if limit is not None:
            params["limit"] = limit

        try:
            url = f"{self.base_url}/detail"
            logging.info(
                f"[BusinessLogicClient] Attempting to GET: {url} with params: {params}"
            )
            response = await self.request_with_retry("get", url, params=params)
            details_data = response.json()
            logging.info(
                f"[BusinessLogicClient] Successfully fetched {len(details_data)} service details."
            )
            return details_data
        except httpx.HTTPStatusError as e:
            logging.error(
                f"[BusinessLogicClient] HTTP error fetching service details: {e.response.status_code} - {e.response.text}"
            )
            return None
        except httpx.RequestError as e:
            logging.error(
                f"[BusinessLogicClient] Request error fetching service details: {e}"
            )
            return None
        except Exception as e:
            logging.error(
                f"[BusinessLogicClient] Unexpected error fetching service details: {e}"
            )
            return None
