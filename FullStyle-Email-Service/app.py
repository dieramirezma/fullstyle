import json
import logging
import os
import time

from flask import Flask, g, request

from config.rabbitmq_config import rabbitmq  # Assuming rabbitmq instance is in rabbitmq_config
from config.server_config import configure_app
from routes.email_routes import email_bp

logger = logging.getLogger(__name__)


def create_email_app():
    app = Flask(__name__)
    from config.identity import configure_identity

    configure_identity(app)
    configure_app(app)  # Basic app configuration

    @app.before_request
    def timing():
        g.started = time.monotonic()

    @app.after_request
    def measure(response):
        app.logger.info(
            json.dumps(
                {
                    "component": "email",
                    "status": response.status_code,
                    "route": str(request.url_rule),
                    "latency_ms": round(
                        (time.monotonic() - getattr(g, "started", time.monotonic())) * 1000, 3
                    ),
                }
            )
        )
        return response

    # Initialize RabbitMQ connection for the app context if needed by routes
    # rabbitmq.connect() # Or handle connection within EmailProducer / EmailWorker

    app.register_blueprint(email_bp)

    logger.info("Email Service Flask app created and blueprints registered.")

    @app.get("/health")
    def health():
        return {"status": "ok", "delivery": os.getenv("DELIVERY_MODE", "disabled")}

    @app.get("/ready")
    def ready():
        try:
            connection = rabbitmq.get_connection()
            connection.close()
            return {"status": "ready"}
        except Exception:
            return {"status": "unavailable"}, 503

    return app


if __name__ == "__main__":
    # This part is usually for local dev, Docker setup might be different
    app = create_email_app()
    # Ensure RabbitMQ is connected before worker starts or routes are hit
    # rabbitmq.connect() # Ensure connection for producer if it's initialized globally
    app.run(host="0.0.0.0", port=5002)  # Example port
