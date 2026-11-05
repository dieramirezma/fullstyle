FROM python:3.13-slim@sha256:ae14d4ce8771606477a81446e7ef429edd6762305fc50c84507c1041fa8285d1
WORKDIR /work
COPY tests/security/requirements.lock /work/requirements.txt
RUN --mount=type=cache,id=fullstyle-portfolio-pip-security,target=/root/.cache/pip pip install -r requirements.txt
COPY FullStyle-Backend/config/db_config.py /work/backend/config/db_config.py
COPY FullStyle-Backend/models /work/backend/models
COPY FullStyle-Backend/services /work/backend/services
COPY FullStyle-Backend/utils /work/backend/utils
COPY FullStyle-Chatbot/app /work/chatbot/app
COPY tests/security /work/tests
ENV PYTHONPATH=/work/chatbot:/work/backend HOST=127.0.0.1 PORT=5000 APP_WEB_URL=http://localhost/ REDIS_HOST=redis
CMD ["python", "-m", "unittest", "discover", "-s", "/work/tests", "-v"]
