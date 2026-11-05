FROM python:3.13-slim@sha256:ae14d4ce8771606477a81446e7ef429edd6762305fc50c84507c1041fa8285d1
WORKDIR /app
COPY FullStyle-Backend/requirements-local.lock requirements.lock
RUN --mount=type=cache,id=fullstyle-portfolio-pip-backend,target=/root/.cache/pip pip install -r requirements.lock
COPY FullStyle-Backend /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
CMD ["gunicorn", "--config", "gunicorn_local.py", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "config.server_config:create_app()"]
