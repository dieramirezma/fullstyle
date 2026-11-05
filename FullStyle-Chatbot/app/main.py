"""Provider-free startup; the configured agent is initialized on authorized use."""

import asyncio
import json
import logging
import os
import re
import time
from contextlib import asynccontextmanager, suppress
from uuid import uuid4

from fastapi import FastAPI, Request

from app.api.v1.endpoints import chat_handler
from app.core.tracing import request_ids
from app.repositories.chat_store import redact_expired


@asynccontextmanager
async def lifespan(_app):
    async def retention():
        while True:
            try:
                await asyncio.to_thread(redact_expired)
            except Exception as exc:
                logging.warning("Chat retention unavailable: %s", type(exc).__name__)
            await asyncio.sleep(60)

    task = asyncio.create_task(retention())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(title="FullStyle Chatbot API", version="1.0.0", lifespan=lifespan)


@app.middleware("http")
async def identifiers(request: Request, call_next):
    started = time.monotonic()
    ids = {}
    for header in ("X-Correlation-ID", "X-Operation-ID"):
        value = request.headers.get(header, "")
        ids[header] = value if re.fullmatch(r"[A-Za-z0-9._-]{1,80}", value) else uuid4().hex
    context = request_ids.set(ids)
    try:
        response = await call_next(request)
        for key, value in ids.items():
            response.headers[key] = value
        logging.getLogger("uvicorn.error").info(
            json.dumps(
                {
                    "component": "chatbot",
                    "status": response.status_code,
                    "latency_ms": round((time.monotonic() - started) * 1000, 3),
                    "correlation_id": ids["X-Correlation-ID"],
                    "operation_id": ids["X-Operation-ID"],
                }
            )
        )
        return response
    finally:
        request_ids.reset(context)


@app.get("/")
@app.get("/health")
async def health():
    return {
        "status": "FullStyle Chatbot is running!",
        "mode": os.getenv("CHAT_MODE", "disabled"),
    }


app.include_router(chat_handler.router, prefix="/api/v1/chat", tags=["Chat V1"])
