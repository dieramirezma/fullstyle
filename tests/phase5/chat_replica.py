"""Local fault fixture; the delay command exists only in disposable test replicas."""

import asyncio

import uvicorn
from app.services.local_agent import local_agent

original = local_agent.generate_text_with_agent


async def controlled(*args, **kwargs):
    if kwargs.get("user_input") == "__phase5_slow__":
        await asyncio.sleep(30)
    return await original(*args, **kwargs)


local_agent.generate_text_with_agent = controlled
uvicorn.run("app.main:app", host="0.0.0.0", port=8080)
