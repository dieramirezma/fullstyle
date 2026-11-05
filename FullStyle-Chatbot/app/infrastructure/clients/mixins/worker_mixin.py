import logging
from typing import Any, Dict, List, Optional

import httpx


class WorkerMethodsMixin:
    async def get_workers(
        self,
        site_id: Optional[int] = None,
        name: Optional[str] = None,
        service_id: Optional[int] = None,
    ) -> List[Dict[str, Any]] | None:
        """
        Fetches workers from the FullStyle Backend API.
        Can filter by site_id, name, and service_id.
        """
        if not self.base_url:
            logging.error(
                "Error: BusinessLogicClient cannot fetch workers, base_url not configured."
            )
            return None

        params = {}
        if site_id is not None:
            params["site_id"] = site_id
        if name:
            params["name"] = name
        if service_id is not None:
            params["service_id"] = service_id

        try:
            url = f"{self.base_url}/worker"
            logging.info(
                f"[BusinessLogicClient] Attempting to GET: {url} with params: {params}"
            )
            response = await self.request_with_retry("get", url, params=params)
            workers_data = response.json()
            logging.info(
                f"[BusinessLogicClient] Successfully fetched {len(workers_data)} workers."
            )
            return workers_data
        except httpx.HTTPStatusError as e:
            logging.error(
                f"[BusinessLogicClient] HTTP error fetching workers: {e.response.status_code} - {e.response.text}"
            )
            return None
        except httpx.RequestError as e:
            logging.error(f"[BusinessLogicClient] Request error fetching workers: {e}")
            return None
        except Exception as e:
            logging.error(
                f"[BusinessLogicClient] Unexpected error fetching workers: {e}"
            )
            return None

    async def get_worker_daily_schedule(
        self, worker_id: int, date: str
    ) -> Dict[str, Any] | None:
        """
        Fetches availability for a specific worker on a given date.
        Uses the endpoint /api/worker/daily_schedule?worker_id=<worker_id>&date=<date>
        The date should be in YYYY-MM-DD format.
        """
        if not self.base_url:
            logging.error(
                "Error: BusinessLogicClient cannot fetch availability, base_url not configured."
            )
            return None

        params = {"worker_id": worker_id, "date": date}
        try:
            url = f"{self.base_url}/worker/daily_schedule"
            logging.info(
                f"[BusinessLogicClient] Attempting to GET: {url} with params: {params}"
            )
            response = await self.request_with_retry("get", url, params=params)
            availability_data = response.json()
            logging.info(
                f"[BusinessLogicClient] Successfully fetched availability for worker {worker_id} on {date}."
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

    async def get_worker_weekly_schedule(
        self, worker_id: int, date: str
    ) -> Dict[str, Any] | None:
        """
        Fetches weekly schedule for a specific worker on a given week.
        Uses the endpoint /api/worker/weekly_schedule?worker_id=<worker_id>&date=<date>
        The date should be in YYYY-MM-DD format and represents any day within the desired week.
        """
        if not self.base_url:
            logging.error(
                "Error: BusinessLogicClient cannot fetch weekly schedule, base_url not configured."
            )
            return None

        params = {"worker_id": worker_id, "date": date}
        try:
            url = f"{self.base_url}/worker/weekly_schedule"
            logging.info(
                f"[BusinessLogicClient] Attempting to GET: {url} with params: {params}"
            )
            response = await self.request_with_retry("get", url, params=params)
            weekly_schedule_data = response.json()
            logging.info(
                f"[BusinessLogicClient] Successfully fetched weekly schedule for worker {worker_id} for week containing {date}."
            )
            return weekly_schedule_data
        except httpx.HTTPStatusError as e:
            logging.error(
                f"[BusinessLogicClient] HTTP error fetching weekly schedule: {e.response.status_code} - {e.response.text}"
            )
            return None
        except httpx.RequestError as e:
            logging.error(
                f"[BusinessLogicClient] Request error fetching weekly schedule: {e}"
            )
            return None
        except Exception as e:
            logging.error(
                f"[BusinessLogicClient] Unexpected error fetching weekly schedule: {e}"
            )
            return None
