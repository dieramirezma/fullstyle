"""
Unit tests for the chat models.
"""
import pytest

from app.domain.models.chat_models import ChatRequest, ChatResponse


def test_chat_request_creation():
    """Test that a ChatRequest can be created with the correct attributes."""
    request = ChatRequest(
        message="Hello, how can I book an appointment?", session_id="test-session"
    )

    assert request.message == "Hello, how can I book an appointment?"
    assert request.session_id == "test-session"


def test_chat_request_missing_message():
    """Test that a ChatRequest cannot be created without a message."""
    with pytest.raises(ValueError):
        ChatRequest(session_id="test-session")


def test_chat_request_optional_session_id():
    """Test that a ChatRequest can be created without a session_id."""
    request = ChatRequest(message="Hello, how can I book an appointment?")

    assert request.message == "Hello, how can I book an appointment?"
    assert request.session_id is None


def test_chat_response_creation():
    """Test that a ChatResponse can be created with the correct attributes."""
    response = ChatResponse(
        reply="I can help you book an appointment. What service are you interested in?",
        session_id="test-session",
    )

    assert (
        response.reply
        == "I can help you book an appointment. What service are you interested in?"
    )
    assert response.session_id == "test-session"
    assert response.debug_info is None
    assert response.error is None


def test_chat_response_with_error():
    """Test that a ChatResponse can include an error message."""
    response = ChatResponse(
        reply="Sorry, I couldn't process your request.",
        session_id="test-session",
        error="Backend API connection failed",
    )

    assert response.reply == "Sorry, I couldn't process your request."
    assert response.error == "Backend API connection failed"


def test_chat_response_with_debug_info():
    """Test that a ChatResponse can include debug information."""
    debug_data = {"execution_time": 0.5, "api_calls": 2}
    response = ChatResponse(
        reply="I found 3 available slots.",
        session_id="test-session",
        debug_info=debug_data,
    )

    assert response.reply == "I found 3 available slots."
    assert response.debug_info == debug_data
