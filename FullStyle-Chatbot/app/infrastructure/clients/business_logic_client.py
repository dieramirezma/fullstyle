"""Backend adapter that preserves the caller's verified identity on every call."""

from urllib.parse import urlsplit

import httpx

from app.core.config import settings
from app.core.identity import require_identity
from app.core.reliability import request as reliable_request
from app.core.tracing import request_ids
from app.infrastructure.clients.mixins.appointment_mixin import AppointmentMethodsMixin
from app.infrastructure.clients.mixins.availability_mixin import (
    AvailabilityMethodsMixin,
)
from app.infrastructure.clients.mixins.category_mixin import CategoryMethodsMixin
from app.infrastructure.clients.mixins.detail_mixin import DetailMethodsMixin
from app.infrastructure.clients.mixins.service_mixin import ServiceMethodsMixin
from app.infrastructure.clients.mixins.site_has_category_mixin import (
    SiteHasCategoryMethodsMixin,
)
from app.infrastructure.clients.mixins.site_mixin import SiteMethodsMixin
from app.infrastructure.clients.mixins.worker_has_service_mixin import (
    WorkerHasServiceMethodsMixin,
)
from app.infrastructure.clients.mixins.worker_mixin import WorkerMethodsMixin


class BusinessLogicClient(
    AppointmentMethodsMixin,
    AvailabilityMethodsMixin,
    CategoryMethodsMixin,
    DetailMethodsMixin,
    ServiceMethodsMixin,
    SiteHasCategoryMethodsMixin,
    SiteMethodsMixin,
    WorkerHasServiceMethodsMixin,
    WorkerMethodsMixin,
):
    def __init__(self):
        self.base_url = settings.API_BASE_URL_DEV.rstrip("/") + "/api"

    async def renew_token(self) -> bool:
        # Kept as a compatible adapter; the client must renew its own session.
        return False

    async def request_with_retry(self, method: str, url: str, **kwargs) -> httpx.Response:
        identity = require_identity()
        target, base = urlsplit(url), urlsplit(self.base_url)
        if (target.scheme, target.netloc) != (
            base.scheme,
            base.netloc,
        ) or not target.path.startswith(base.path + "/"):
            raise PermissionError("Delegation is restricted to the configured backend")
        headers = {
            key: value
            for key, value in kwargs.pop("headers", {}).items()
            if key.lower() != "authorization"
        }
        headers.update(request_ids.get())
        headers["Authorization"] = identity.authorization
        response = await reliable_request(method, url, headers=headers, **kwargs)
        # Never log in as a service user or retry a rejected write under another identity.
        response.raise_for_status()
        return response
