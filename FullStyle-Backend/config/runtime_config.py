"""Application factory: configuration and connections are explicit at runtime."""

import importlib
import logging
import os
from datetime import timedelta

from flask import Flask, jsonify
from flask_cors import CORS
from flask_restful import Api
from sqlalchemy import text

from config.db_config import db
from utils.observability import configure_observability
from utils.sessions import configure_sessions


def create_app(overrides=None):
    app = Flask(__name__, template_folder="../templates")
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        MFA_KEYRING_FILE=os.environ.get("MFA_KEYRING_FILE"),
        JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={
            "pool_pre_ping": True,
            "connect_args": {
                "connect_timeout": 3,
                "options": "-c statement_timeout=15000 -c lock_timeout=5000",
            },
        },
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=1),
        JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=15),
        MAX_CONTENT_LENGTH=1_048_576,
        PROPAGATE_EXCEPTIONS=True,
    )
    app.config.update(overrides or {})
    if not all(
        app.config.get(key) for key in ("SECRET_KEY", "JWT_SECRET_KEY", "SQLALCHEMY_DATABASE_URI")
    ):
        raise ValueError("SECRET_KEY, JWT_SECRET_KEY and DATABASE_URL are required")
    logging.basicConfig(level=logging.INFO)
    CORS(app, origins=os.getenv("CORS_ORIGIN", "http://localhost:38080").split(","))
    for model in (
        "user",
        "client",
        "manager",
        "site",
        "category",
        "service",
        "worker",
        "detail",
        "appointment",
        "availability",
        "days_off",
        "seasonal_schedule",
        "worker_has_service",
        "site_has_category",
        "payment",
        "notification",
        "session",
        "consistency",
        "reliability",
        "account_security",
        "completion",
    ):
        importlib.import_module(f"models.{model}_model")
    db.init_app(app)
    configure_sessions(app)
    configure_observability(app)
    from config.routes_config import start_routes
    from services.completion_service import completion
    from services.integration_service import integrations
    from services.session_service import sessions

    start_routes(Api(app))
    app.register_blueprint(sessions)
    app.register_blueprint(integrations)
    app.register_blueprint(completion)

    @app.get("/api/swagger.json")
    def swagger():
        from config.swagger_config import get_apidocs

        return jsonify(get_apidocs())

    @app.get("/api/docs")
    def docs():
        return '<a href="/api/swagger.json">FullStyle OpenAPI</a>'

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.get("/ready")
    def ready():
        try:
            version = db.session.execute(
                text("SELECT version FROM schema_migration ORDER BY version DESC LIMIT 1")
            ).scalar_one()
            if version != "0005_local_completion":
                return jsonify(status="migration-required"), 503
            return jsonify(status="ready")
        except Exception:
            db.session.rollback()
            return jsonify(status="unavailable"), 503

    return app


def run_server():
    create_app().run(host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", "5000")))
