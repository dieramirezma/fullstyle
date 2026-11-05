import logging
from typing import Any, Dict, List, Optional

import httpx


class WorkerHasServiceMethodsMixin:
    async def get_worker_has_service(
        self,
        worker_id: Optional[int] = None,
        service_id: Optional[int] = None,
    ) -> List[Dict[str, Any]] | None:
        """
        Fetches worker-service relationships from the FullStyle Backend API.
        Can filter by worker_id, service_id, or both.
        """
        if not self.base_url:
            logging.error(
                "Error: BusinessLogicClient cannot fetch worker-service relationships, base_url not configured."
            )
            return None

        params = {}
        if worker_id is not None:
            params["worker_id"] = worker_id
        if service_id is not None:
            params["service_id"] = service_id

        try:
            url = f"{self.base_url}/worker_has_service"
            logging.info(
                f"[BusinessLogicClient] Attempting to GET: {url} with params: {params}"
            )
            response = await self.request_with_retry("get", url, params=params)
            worker_services_data = response.json()
            logging.info(
                f"[BusinessLogicClient] Successfully fetched {len(worker_services_data)} worker-service relationships."
            )
            return worker_services_data
        except httpx.HTTPStatusError as e:
            logging.error(
                f"[BusinessLogicClient] HTTP error fetching worker-service relationships: {e.response.status_code} - {e.response.text}"
            )
            return None
        except httpx.RequestError as e:
            logging.error(
                f"[BusinessLogicClient] Request error fetching worker-service relationships: {e}"
            )
            return None
        except Exception as e:
            logging.error(
                f"[BusinessLogicClient] Unexpected error fetching worker-service relationships: {e}"
            )
            return None
