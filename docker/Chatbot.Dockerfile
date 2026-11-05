FROM python:3.13-slim@sha256:ae14d4ce8771606477a81446e7ef429edd6762305fc50c84507c1041fa8285d1
WORKDIR /app
COPY FullStyle-Chatbot/requirements-local.lock requirements.lock
RUN --mount=type=cache,id=fullstyle-portfolio-pip-chatbot,target=/root/.cache/pip pip install -r requirements.lock
COPY FullStyle-Chatbot/app /app/app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
