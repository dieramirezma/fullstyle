"""Request-scoped delegation; no shared account or unverified user ID fallback."""

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Annotated

import httpx
from fastapi import Header, HTTPException

from app.core.config import settings
from app.core.reliability import request as reliable_request
from app.core.tracing import request_ids


@dataclass(frozen=True)
class Identity:
    user_id: int
    authorization: str


current_identity: ContextVar[Identity | None] = ContextVar("fullstyle_identity", default=None)


def require_identity():
    identity = current_identity.get()
    if identity is None:
        raise PermissionError("An authenticated user is required")
    return identity


async def delegated_identity(authorization: Annotated[str | None, Header()] = None):
    if (
        not authorization
        or not authorization.startswith("Bearer ")
        or not authorization[7:].strip()
    ):
        raise HTTPException(status_code=401, detail="Bearer identity required")
    try:
        response = await reliable_request(
            "GET",
            settings.API_BASE_URL_DEV.rstrip("/") + "/api/me",
            headers={**request_ids.get(), "Authorization": authorization},
        )
        if response.status_code in (401, 403, 422):
            raise HTTPException(status_code=401, detail="Invalid or expired identity")
        response.raise_for_status()
        user = response.json()
        if type(user.get("id")) is not int or user["id"] <= 0 or user.get("active") is not True:
            raise HTTPException(status_code=401, detail="Invalid identity")
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        raise HTTPException(status_code=503, detail="Identity verification unavailable") from exc
    identity = Identity(user["id"], authorization)
    token = current_identity.set(identity)
    try:
        yield identity
    finally:
        current_identity.reset(token)
