# FullStyle-email_service

Email microservice for the FullStyle application. This service is responsible for handling all email-sending functionalities, such as subscription confirmations, password resets, appointment notifications, and contact form submissions.

## Architecture and Workflow

The `FullStyle-email_service` is designed to be a standalone microservice that integrates with the main `FullStyle-Backend` and uses RabbitMQ for asynchronous task processing.

1.  **HTTP API Endpoints**: The service exposes HTTP POST endpoints (e.g., `/api/emails/subscription`, `/api/emails/reset-password`). Other services, primarily the `FullStyle-Backend`, send requests to these endpoints to trigger email dispatches.
2.  **RabbitMQ Integration**:
    *   Upon receiving an HTTP request, the `email-api` component of this service (running `app.py`) validates the request and publishes a message to a specific RabbitMQ queue (`email_queue`). This decouples the HTTP request handling from the actual email sending process, making the API calls fast and resilient.
    *   The RabbitMQ broker itself is defined and managed within the `docker-compose.yaml` of the `FullStyle-Backend` service. The `FullStyle-email_service` connects to this RabbitMQ instance.
3.  **Asynchronous Email Processing**:
    *   The `email-worker` component of this service (running `workers/email_worker.py`) is a dedicated consumer that listens to the `email_queue` on RabbitMQ.
    *   When a new message appears in the queue, the worker picks it up, processes the email details (e.g., recipient, subject, template), and uses the Resend API to send the email.
4.  **Email Sending**: The actual email sending is handled by the `EmailService` class, which interacts with the Resend API (https://resend.com).

This architecture ensures that email sending operations are handled reliably and do not block the primary application flow.

```mermaid
sequenceDiagram
    participant Backend as FullStyle-Backend
    participant EmailAPI as FullStyle-email_service (API)
    participant RabbitMQ
    participant EmailWorker as FullStyle-email_service (Worker)
    participant Resend

    Backend->>+EmailAPI: HTTP POST /api/emails/... (e.g., subscription)
    EmailAPI->>+RabbitMQ: Publish message to email_queue
    EmailAPI-->>-Backend: HTTP 200 OK (queued)
    RabbitMQ-->>+EmailWorker: Deliver message from email_queue
    EmailWorker->>+Resend: Send email request
    Resend-->>-EmailWorker: Email sent/failed
    EmailWorker-->>-RabbitMQ: Acknowledge message
```

## Prerequisites

*   Docker and Docker Compose installed.
*   A `.env` file in the root of the `FullStyle-email_service` directory with the necessary environment variables (see [Environment Variables](#environment-variables) section).
*   The `FullStyle-Backend` service, particularly its RabbitMQ instance, should be running.

## Setup and Running the Service

1.  **Start RabbitMQ (from FullStyle-Backend)**:
    Navigate to the `FullStyle-Backend` directory and start the RabbitMQ service:
    ```bash
    cd path/to/FULLSTYLE/FullStyle-API-Gateway/FullStyle-Backend
    docker-compose up -d rabbitmq
    ```
    Ensure RabbitMQ is healthy. You can check its management interface at `http://localhost:15672` (default credentials: `admin`/`password` as per `FullStyle-Backend/docker-compose.yaml`).

2.  **Configure Environment Variables for `FullStyle-email_service`**:
    Create a `.env` file in the `FullStyle-email_service` root directory (e.g., `FullStyle-email_service/.env`). Add the following variables:
    ```env
    # .env for FullStyle-email_service
    HOST=0.0.0.0
    PORT=5001
    ENV=development
    PYTHONUNBUFFERED=1

    # This key is for Flask app security, can be any random string.
    # Ensure it's consistent if used for session or other security features.
    SECRET_KEY=your_flask_secret_key_here

    # Your Resend API key for sending emails
    RESEND_API_KEY=your_resend_api_key_here

    # URL for the RabbitMQ instance started by FullStyle-Backend
    # 'host.docker.internal' allows Docker containers (on Docker Desktop for Mac/Windows)
    # to connect to services running on the host, or in this case, another Docker container
    # exposed on the host's network.
    RABBITMQ_URL=amqp://admin:password@host.docker.internal:5672
    ```
    Replace `your_flask_secret_key_here` and `your_resend_api_key_here` with your actual keys.

3.  **Run `FullStyle-email_service`**:
    Navigate to the `FullStyle-email_service` directory and start the services (API and worker) using Docker Compose:
    ```bash
    cd path/to/FULLSTYLE/FullStyle-API-Gateway/FullStyle-email_service
    docker-compose up -d --build
    ```
    This will build the Docker images if they don't exist and start the `email-api` and `email-worker` containers.
    *   The `email-api` will be accessible on port `5001` (e.g., `http://localhost:5001`).
    *   The `email-worker` will connect to RabbitMQ and start processing messages.

    You can view logs using:
    ```bash
    docker-compose logs -f email-api
    docker-compose logs -f email-worker
    ```

## API Endpoints and Testing with cURL

The service exposes several endpoints under the `/api/emails` prefix. All endpoints are `POST` requests and expect a JSON payload.

**Base URL**: `http://localhost:5001`

Here are some examples:

1.  **Send Subscription Email**:
    *   Endpoint: `/api/emails/subscription`
    *   Payload:
        ```json
        {
            "owner_email": "test@example.com",
            "owner_name": "John Doe",
            "subscription_plan": "Premium Plan",
            "payment_date": "2024-07-15",
            "finish_date": "2025-07-15"
        }
        ```
    *   cURL command:
        ```bash
        curl -X POST -H "Content-Type: application/json" \
        -d '{
              "owner_email": "test@example.com",
              "owner_name": "John Doe",
              "subscription_plan": "Premium Plan",
              "payment_date": "2024-07-15",
              "finish_date": "2025-07-15"
            }' \
        http://localhost:5001/api/emails/subscription
        ```

2.  **Send Reset Password Email**:
    *   Endpoint: `/api/emails/reset-password`
    *   Payload:
        ```json
        {
            "email": "user@example.com",
            "name": "Jane Doe"
        }
        ```
    *   cURL command:
        ```bash
        curl -X POST -H "Content-Type: application/json" \
        -d '{
              "email": "user@example.com",
              "name": "Jane Doe"
            }' \
        http://localhost:5001/api/emails/reset-password
        ```

3.  **Send Contact Email**:
    *   Endpoint: `/api/emails/contact`
    *   Payload:
        ```json
        {
            "name": "Visitor Name",
            "email": "visitor@example.com",
            "message": "Hello, I have a question."
        }
        ```
    *   cURL command:
        ```bash
        curl -X POST -H "Content-Type: application/json" \
        -d '{
              "name": "Visitor Name",
              "email": "visitor@example.com",
              "message": "Hello, I have a question."
            }' \
        http://localhost:5001/api/emails/contact
        ```

4.  **Send Appointment Confirmation Email**:
    *   Endpoint: `/api/emails/appointment/confirmation`
    *   Payload (example, refer to `email_service.py` for all fields):
        ```json
        {
            "customer_email": "customer@example.com",
            "customer_name": "Customer Name",
            "site_name": "Beauty Salon",
            "site_address": "123 Main St",
            "site_phone": "555-1234",
            "service_name": "Haircut",
            "service_description": "Standard haircut service",
            "worker_name": "Stylist Jane",
            "appointment_date": "2024-07-20",
            "appointment_time": "10:00 AM",
            "service_price": "50.00",
            "service_duration": "60"
        }
        ```
    *   cURL command (adjust payload as needed):
        ```bash
        curl -X POST -H "Content-Type: application/json" \
        -d '{
              "customer_email": "customer@example.com",
              "customer_name": "Customer Name",
              "site_name": "Beauty Salon",
              "site_address": "123 Main St",
              "site_phone": "555-1234",
              "service_name": "Haircut",
              "service_description": "Standard haircut service",
              "worker_name": "Stylist Jane",
              "appointment_date": "2024-07-20",
              "appointment_time": "10:00 AM",
              "service_price": "50.00",
              "service_duration": "60"
            }' \
        http://localhost:5001/api/emails/appointment/confirmation
        ```

**Other Appointment-Related Endpoints**:
These follow a similar pattern, expecting relevant data for the email type.
*   `/api/emails/appointment/partial-payment`
*   `/api/emails/appointment/rejected`
*   `/api/emails/appointment/canceled`

Refer to `routes/email_routes.py` and `services/email_service.py` for the exact payload structures required by each endpoint and the data used in email templates.

## Environment Variables

The following environment variables are used by the `FullStyle-email_service` and should be defined in a `.env` file in the service's root directory:

*   `HOST`: Host address for the Flask API server (e.g., `0.0.0.0`).
*   `PORT`: Port for the Flask API server (e.g., `5001`).
*   `ENV`: Application environment (e.g., `development`, `production`).
*   `PYTHONUNBUFFERED`: Set to `1` to ensure Python output (like logs) is sent straight to stdout/stderr without buffering, which is useful in Docker.
*   `SECRET_KEY`: A secret key used by Flask for session management and other security purposes.
*   `RESEND_API_KEY`: Your API key from Resend (https://resend.com) for sending emails.
*   `RABBITMQ_URL`: The connection URL for the RabbitMQ instance. When running RabbitMQ via Docker from `FullStyle-Backend` and `FullStyle-email_service` via Docker on the same machine (using Docker Desktop), this is typically `amqp://admin:password@host.docker.internal:5672`.

## Project Structure

*   `app.py`: Main Flask application setup for the API.
*   `config/`: Configuration files.
    *   `server_config.py`: Flask app configurations.
    *   `rabbitmq_config.py`: RabbitMQ connection logic.
*   `routes/`: API route definitions.
    *   `email_routes.py`: Defines all `/api/emails/*` endpoints.
*   `services/`: Business logic.
    *   `email_service.py`: Handles the actual email construction and sending via Resend.
*   `workers/`: Background worker processes.
    *   `email_worker.py`: Consumes messages from RabbitMQ and uses `EmailService` to send emails.
*   `templates/`: HTML email templates (though not explicitly listed in the provided structure, typically where Resend templates might be managed or referenced if using local HTML rendering before sending to Resend).
*   `Dockerfile`: Instructions to build the Docker image for the service.
*   `docker-compose.yaml`: Defines the `email-api` and `email-worker` services for Docker Compose.
*   `requirements.txt`: Python dependencies.

## Troubleshooting

*   **Cannot connect to RabbitMQ**:
    *   Ensure the RabbitMQ container from `FullStyle-Backend` is running and healthy.
    *   Verify the `RABBITMQ_URL` in your `FullStyle-email_service/.env` file is correct. If not using Docker Desktop, `host.docker.internal` might not work. You may need to use the host's IP address or set up a Docker network.
    *   Check RabbitMQ logs: `docker logs <rabbitmq_container_id_or_name>`
*   **Emails not being sent**:
    *   Check `email-worker` logs: `docker-compose logs -f email-worker` in the `FullStyle-email_service` directory.
    *   Verify your `RESEND_API_KEY` is correct and has permissions.
    *   Check the Resend dashboard for any API errors or delivery issues.
*   **API returning errors**:
    *   Check `email-api` logs: `docker-compose logs -f email-api`.
    *   Ensure the JSON payload in your cURL requests is correctly formatted.