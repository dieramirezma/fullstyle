"""Tracing metadata is isolated with the same request lifetime as user delegation."""

from contextvars import ContextVar

request_ids: ContextVar[dict[str, str]] = ContextVar("request_ids", default={})
