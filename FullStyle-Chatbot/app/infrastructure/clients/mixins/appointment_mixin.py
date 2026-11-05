import logging
from typing import Any, Dict, List, Optional

import httpx


class AppointmentMethodsMixin:
    async def post_appointment(
        self, reservation_data: Dict[str, Any]
    ) -> Dict[str, Any] | None:
        """
        Creates a reservation using the FullStyle Backend API.
        Assumes the endpoint is /api/appointment
        reservation_data should conform to the backend's expected model for creating an appointment.
        Example:
        {
            "client_id": int,
            "worker_id": int,
            "service_id": int,
            "site_id": int,
            "appointment_time": "YYYY-MM-DD HH:MM:SS",
            "status": "pending",
            "request": bool (optional, default False)
        }
        If request=True, only validates availability without creating the appointment.
        """
        if not self.base_url:
            logging.error(
                "Error: BusinessLogicClient cannot create/validate reservation, base_url not configured."
            )
            return None

        try:
            url = f"{self.base_url}/appointment"
            is_validation_only = reservation_data.get("request", False)
            action = "validate" if is_validation_only else "create"

            logging.info(
                f"[BusinessLogicClient] Attempting to {action} appointment at: {url} with data: {reservation_data}"
            )
            response = await self.request_with_retry("post", url, json=reservation_data)

            if is_validation_only:
                # For validation requests, the response should be True/False or error message
                result = response.json()
                logging.info(
                    f"[BusinessLogicClient] Appointment validation result: {result}"
                )
                return {"validation_result": result, "is_available": result is True}
            else:
                # For actual creation, return the created appointment
                created_appointment = response.json()
                logging.info(
                    f"[BusinessLogicClient] Successfully created appointment: {created_appointment.get('id')}"
                )
                return created_appointment

        except httpx.HTTPStatusError as e:
            logging.error(
                f"[BusinessLogicClient] HTTP error with appointment: {e.response.status_code} - {e.response.text}"
            )
            return {"error": e.response.text, "status_code": e.response.status_code}
        except httpx.RequestError as e:
            logging.error(f"[BusinessLogicClient] Request error with appointment: {e}")
            return None
        except Exception as e:
            logging.error(
                f"[BusinessLogicClient] Unexpected error with appointment: {e}"
            )
            return None

    async def get_appointments(
        self,
        id: Optional[int] = None,
        status: Optional[str] = None,
        worker_id: Optional[int] = None,
        site_id: Optional[int] = None,
        service_id: Optional[int] = None,
        client_id: Optional[int] = None,
    ) -> List[Dict[str, Any]] | None:
        """
        Fetches appointments from the FullStyle Backend API.
        Can filter by id, status, worker_id, site_id, service_id, client_id.
        """
        if not self.base_url:
            logging.error(
                "Error: BusinessLogicClient cannot fetch appointments, base_url not configured."
            )
            return None

        params = {}
        if id is not None:
            params["id"] = id
        if status:
            params["status"] = status
        if worker_id is not None:
            params["worker_id"] = worker_id
        if site_id is not None:
            params["site_id"] = site_id
        if service_id is not None:
            params["service_id"] = service_id
        if client_id is not None:
            params["client_id"] = client_id

        try:
            url = f"{self.base_url}/appointment"
            logging.info(
                f"[BusinessLogicClient] Attempting to GET: {url} with params: {params}"
            )
            response = await self.request_with_retry("get", url, params=params)
            appointments_data = response.json()
            logging.info(
                f"[BusinessLogicClient] Successfully fetched {len(appointments_data)} appointments."
            )
            return appointments_data
        except httpx.HTTPStatusError as e:
            logging.error(
                f"[BusinessLogicClient] HTTP error fetching appointments: {e.response.status_code} - {e.response.text}"
            )
            return None
        except httpx.RequestError as e:
            logging.error(
                f"[BusinessLogicClient] Request error fetching appointments: {e}"
            )
            return None
        except Exception as e:
            logging.error(
                f"[BusinessLogicClient] Unexpected error fetching appointments: {e}"
            )
            return None

    async def put_appointment(
        self, appointment_id: int, appointment_data: Dict[str, Any]
    ) -> Dict[str, Any] | None:
        """
        Updates an existing appointment using the FullStyle Backend API.
        """
        if not self.base_url:
            logging.error(
                "Error: BusinessLogicClient cannot update appointment, base_url not configured."
            )
            return None

        try:
            url = f"{self.base_url}/appointment"
            params = {"id": appointment_id}

            # Add the ID to the data payload as well (backend expects it)
            appointment_data_with_id = {**appointment_data, "id": appointment_id}

            logging.info(
                f"[BusinessLogicClient] Attempting to PUT: {url} with params: {params} and data: {appointment_data_with_id}"
            )
            response = await self.request_with_retry(
                "put", url, params=params, json=appointment_data_with_id
            )
            updated_appointment = response.json()
            logging.info(
                f"[BusinessLogicClient] Successfully updated appointment: {updated_appointment.get('id')}"
            )
            return updated_appointment

        except httpx.HTTPStatusError as e:
            logging.error(
                f"[BusinessLogicClient] HTTP error updating appointment: {e.response.status_code} - {e.response.text}"
            )
            return {"error": e.response.text, "status_code": e.response.status_code}
        except httpx.RequestError as e:
            logging.error(
                f"[BusinessLogicClient] Request error updating appointment: {e}"
            )
            return None
        except Exception as e:
            logging.error(
                f"[BusinessLogicClient] Unexpected error updating appointment: {e}"
            )
            return None

    async def delete_appointment(self, appointment_id: int) -> Dict[str, Any] | None:
        """
        Deletes an appointment using the FullStyle Backend API.
        """
        if not self.base_url:
            logging.error(
                "Error: BusinessLogicClient cannot delete appointment, base_url not configured."
            )
            return None

        try:
            url = f"{self.base_url}/appointment"
            params = {"id": appointment_id}

            logging.info(
                f"[BusinessLogicClient] Attempting to DELETE: {url} with params: {params}"
            )
            response = await self.request_with_retry("delete", url, params=params)
            result = response.json()
            logging.info(
                f"[BusinessLogicClient] Successfully deleted appointment {appointment_id}"
            )
            return result

        except httpx.HTTPStatusError as e:
            logging.error(
                f"[BusinessLogicClient] HTTP error deleting appointment: {e.response.status_code} - {e.response.text}"
            )
            return {"error": e.response.text, "status_code": e.response.status_code}
        except httpx.RequestError as e:
            logging.error(
                f"[BusinessLogicClient] Request error deleting appointment: {e}"
            )
            return None
        except Exception as e:
            logging.error(
                f"[BusinessLogicClient] Unexpected error deleting appointment: {e}"
            )
            return None

    async def get_appointment_details(
        self,
        id: Optional[int] = None,
        status: Optional[str] = None,
        worker_id: Optional[int] = None,
        site_id: Optional[int] = None,
        service_id: Optional[int] = None,
        client_id: Optional[int] = None,
    ) -> List[Dict[str, Any]] | None:
        """
        Fetches detailed appointment information from the FullStyle Backend API.
        Returns expanded data with worker, site, and service details.
        """
        if not self.base_url:
            logging.error(
                "Error: BusinessLogicClient cannot fetch appointment details, base_url not configured."
            )
            return None

        params = {}
        if id is not None:
            params["id"] = id
        if status:
            params["status"] = status
        if worker_id is not None:
            params["worker_id"] = worker_id
        if site_id is not None:
            params["site_id"] = site_id
        if service_id is not None:
            params["service_id"] = service_id
        if client_id is not None:
            params["client_id"] = client_id

        try:
            url = f"{self.base_url}/appointmentdetail"
            logging.info(
                f"[BusinessLogicClient] Attempting to GET: {url} with params: {params}"
            )
            response = await self.request_with_retry("get", url, params=params)
            appointment_details = response.json()
            logging.info(
                f"[BusinessLogicClient] Successfully fetched {len(appointment_details)} appointment details."
            )
            return appointment_details
        except httpx.HTTPStatusError as e:
            logging.error(
                f"[BusinessLogicClient] HTTP error fetching appointment details: {e.response.status_code} - {e.response.text}"
            )
            return None
        except httpx.RequestError as e:
            logging.error(
                f"[BusinessLogicClient] Request error fetching appointment details: {e}"
            )
            return None
        except Exception as e:
            logging.error(
                f"[BusinessLogicClient] Unexpected error fetching appointment details: {e}"
            )
            return None

    async def validate_appointment_availability(
        self, reservation_data: Dict[str, Any]
    ) -> Dict[str, Any] | None:
        """
        Validates if an appointment can be scheduled without actually creating it.
        This is a convenience method that sets request=True automatically.
        """
        validation_data = reservation_data.copy()
        validation_data["request"] = True
        return await self.post_appointment(validation_data)
