"""Additive request identifiers. Operation IDs are tracing, not idempotency keys."""

import json
import re
import time
from uuid import uuid4

from flask import g, request


def configure_observability(app):
    @app.before_request
    def identify_request():
        g.request_started = time.monotonic()
        for header, attribute in (
            ("X-Correlation-ID", "correlation_id"),
            ("X-Operation-ID", "operation_id"),
        ):
            supplied = request.headers.get(header, "")
            setattr(
                g,
                attribute,
                supplied if re.fullmatch(r"[A-Za-z0-9._-]{1,80}", supplied) else uuid4().hex,
            )

    @app.after_request
    def identify_response(response):
        response.headers["X-Correlation-ID"] = g.correlation_id
        response.headers["X-Operation-ID"] = g.operation_id
        app.logger.info(
            json.dumps(
                {
                    "component": "backend",
                    "route": str(request.url_rule),
                    "method": request.method,
                    "status": response.status_code,
                    "conflict": response.status_code == 409,
                    "latency_ms": round((time.monotonic() - g.request_started) * 1000, 3),
                    "correlation_id": g.correlation_id,
                    "operation_id": g.operation_id,
                }
            )
        )
        return response
