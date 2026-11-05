"""Bounded retries for reads only. Mutations, auth failures and 4xx are never retried."""

import asyncio
import json
import logging
import time

import httpx


async def request(method, url, **kwargs):
    safe = method.upper() in {"GET", "HEAD"}
    attempts = 2 if safe else 1
    started = time.monotonic()
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(5, connect=2, pool=1), trust_env=False, follow_redirects=False
    ) as client:
        for attempt in range(attempts):
            try:
                response = await client.request(method, url, **kwargs)
                if not (
                    safe and response.status_code in {502, 503, 504} and attempt + 1 < attempts
                ):
                    logging.info(
                        json.dumps(
                            {
                                "component": "chat-http",
                                "method": method,
                                "status": response.status_code,
                                "attempts": attempt + 1,
                                "latency_ms": round((time.monotonic() - started) * 1000, 3),
                            }
                        )
                    )
                    return response
            except (httpx.ConnectError, httpx.TimeoutException):
                if attempt + 1 == attempts:
                    raise
            await asyncio.sleep(0.1)
