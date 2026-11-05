"""Mail publishing accepts only short-lived payload-bound service capabilities."""

import hashlib
import hmac
import json
import os

import jwt
from flask import g, jsonify, request


def canonical(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def configure_identity(app):
    app.config["MAX_CONTENT_LENGTH"] = 65536

    @app.before_request
    def authorize_publish():
        if request.path in ("/health", "/ready"):
            return None
        try:
            payload = request.get_json(silent=True)
            claims = jwt.decode(
                request.headers.get("Authorization", "").removeprefix("Bearer "),
                os.environ["INTEGRATION_SECRET"],
                algorithms=["HS256"],
                audience="mail.publish",
                options={"require": ["exp", "iat", "sub", "type", "sha256", "jti"]},
            )
            digest = hashlib.sha256(canonical(payload).encode()).hexdigest()
            if (
                claims["type"] != "service"
                or claims["sub"] != "fullstyle-business"
                or not hmac.compare_digest(digest, claims["sha256"])
            ):
                raise ValueError("Invalid service capability")
            if not isinstance(payload, dict):
                return jsonify(message="JSON object required"), 400
        except (jwt.PyJWTError, ValueError):
            return jsonify(message="Restricted mail service identity required"), 401
        g.mail_operation = str(claims.get("operation_id", claims["jti"]))
        return None

    @app.after_request
    def request_ids(response):
        from uuid import uuid4

        for header in ("X-Correlation-ID", "X-Operation-ID"):
            value = request.headers.get(header, "")
            response.headers[header] = (
                value if value.isascii() and 0 < len(value) <= 80 else uuid4().hex
            )
        return response
