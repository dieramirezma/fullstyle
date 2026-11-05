import asyncio
import logging
import os
import re
from uuid import uuid4

import httpx
import psycopg2
from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.identity import Identity, delegated_identity
from app.core.tracing import request_ids
from app.domain.models.chat_models import ChatRequest, ChatResponse
from app.repositories.chat_store import Conversation, StoreError, history, review

router = APIRouter()


def get_llm_service():
    if os.getenv("LOCAL_RUNTIME") == "true" and os.getenv("CHAT_MODE") == "local":
        from app.services.local_agent import local_agent

        return local_agent
    if os.getenv("CHAT_MODE") != "provider":
        raise HTTPException(status_code=503, detail="Chat provider disabled")
    # Delay provider/model initialization until after caller identity is verified.
    from app.services.llm_service import llm_service

    return llm_service


@router.post("/send", response_model=ChatResponse)
async def handle_chat_message(
    request: ChatRequest = Body(...), identity: Identity = Depends(delegated_identity)
):
    """
    Receives a user message, processes it with the Langchain agent via LLMService,
    and returns the agent's reply.
    """
    if not request.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    session_id = request.session_id or uuid4().hex
    operation_id = request_ids.get().get("X-Operation-ID", uuid4().hex)
    turn = Conversation(identity.user_id, session_id, operation_id, request.message)
    try:
        # Only short SQL calls run in threads. No automatic retry can execute a tool twice.
        previous, context = await asyncio.to_thread(turn.begin)
        if turn.replayed:
            return ChatResponse(reply=previous, session_id=session_id)
        async with asyncio.timeout(12):
            reply = await get_llm_service().generate_text_with_agent(
                user_input=request.message,
                session_id=f"{identity.user_id}:{session_id}",
                history=context,
            )
        await asyncio.to_thread(turn.complete, reply)
        return ChatResponse(reply=reply, session_id=session_id)
    except StoreError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except HTTPException:
        raise
    except (psycopg2.Error, httpx.HTTPError, TimeoutError) as exc:
        raise HTTPException(
            status_code=503, detail="Chat dependency unavailable; operation was not retried"
        ) from exc
    except Exception as exc:
        logging.error("Chat execution failed: %s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Chat execution unavailable") from exc
    finally:
        await asyncio.to_thread(turn.close)


@router.get("/history/{session_id}")
async def get_history(session_id: str, identity: Identity = Depends(delegated_identity)):
    if not re.fullmatch(r"[A-Za-z0-9._:-]{1,120}", session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID")
    try:
        turns = await asyncio.to_thread(history, identity.user_id, session_id)
        return {"session_id": session_id, "turns": turns}
    except StoreError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except psycopg2.Error as exc:
        raise HTTPException(status_code=503, detail="Shared history unavailable") from exc


class ReviewRequest(BaseModel):
    note: str = Field(min_length=1, max_length=500)
    checked_booking_state: bool


@router.post("/history/{session_id}/operations/{operation_id}/review")
async def review_operation(
    session_id: str,
    operation_id: str,
    body: ReviewRequest,
    identity: Identity = Depends(delegated_identity),
):
    if (
        not re.fullmatch(r"[A-Za-z0-9._:-]{1,120}", session_id)
        or not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", operation_id)
        or not body.checked_booking_state
        or not body.note.strip()
    ):
        raise HTTPException(
            status_code=400, detail="Valid operation and explicit booking review required"
        )
    try:
        return await asyncio.to_thread(
            review, identity.user_id, session_id, operation_id, body.note
        )
    except StoreError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except psycopg2.Error as exc:
        raise HTTPException(status_code=503, detail="Review storage unavailable") from exc
