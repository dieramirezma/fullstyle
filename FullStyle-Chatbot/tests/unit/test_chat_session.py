"""
Unit tests for chat session management in the LLMService.
"""
import pytest

from app.domain.models.chat_models import ChatRequest, ChatResponse
from app.services.llm_service import LLMService


def test_chat_request_creation():
    """Test that a ChatRequest can be created with a session ID."""
    request = ChatRequest(message="I need a haircut", session_id="test-session-123")

    assert request.message == "I need a haircut"
    assert request.session_id == "test-session-123"


def test_chat_response_creation():
    """Test that a ChatResponse can be created with a session ID."""
    response = ChatResponse(
        reply="I can help you schedule a haircut.", session_id="test-session-123"
    )

    assert response.reply == "I can help you schedule a haircut."
    assert response.session_id == "test-session-123"


@pytest.mark.asyncio
async def test_llm_service_chat_history_management():
    """Test that the LLMService manages chat history properly."""
    # Create an LLMService instance
    llm_service = LLMService()
    session_id = "test-session-history"

    # Initially, there should be no chat history for this session
    assert session_id not in llm_service.chat_histories

    # Process a message
    reply1 = await llm_service.generate_text_with_agent(
        user_input="Hello", session_id=session_id
    )

    # Verify chat history was created
    assert session_id in llm_service.chat_histories
    history = llm_service.chat_histories[session_id]
    assert len(history) == 2  # One user message and one AI response
    assert history[0][0] == "human"
    assert history[0][1] == "Hello"
    assert history[1][0] == "ai"
    assert history[1][1] == reply1


@pytest.mark.asyncio
async def test_llm_service_maintains_conversation_context():
    """Test that the LLMService maintains conversation context across multiple messages."""
    # Create an LLMService instance
    llm_service = LLMService()
    session_id = "test-session-context"

    # Send first message
    await llm_service.generate_text_with_agent(
        user_input="I'm looking for a haircut", session_id=session_id
    )

    # Send follow-up message
    await llm_service.generate_text_with_agent(
        user_input="When is a good time?", session_id=session_id
    )

    # Verify chat history contains the full conversation
    history = llm_service.chat_histories[session_id]
    assert len(history) == 4  # Two user messages and two AI responses

    # The history should include both messages
    user_messages = [msg for role, msg in history if role == "human"]
    assert "I'm looking for a haircut" in user_messages
    assert "When is a good time?" in user_messages


@pytest.mark.asyncio
async def test_llm_service_different_sessions_isolated():
    """Test that different session IDs have isolated chat histories."""
    # Create an LLMService instance
    llm_service = LLMService()

    # Create two different sessions
    session1 = "test-session-1"
    session2 = "test-session-2"

    # Send messages to both sessions
    await llm_service.generate_text_with_agent(
        user_input="I need a haircut", session_id=session1
    )

    await llm_service.generate_text_with_agent(
        user_input="I'm looking for information about barbers", session_id=session2
    )
    # Verify each session has its own separate history
    history1 = llm_service.chat_histories[session1]
    history2 = llm_service.chat_histories[session2]

    assert history1 != history2
    assert "I need a haircut" in history1[0][1]
    assert "I'm looking for information about barbers" in history2[0][1]
