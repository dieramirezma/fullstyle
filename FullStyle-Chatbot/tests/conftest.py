"""
Pytest fixtures for FullStyle Chatbot tests.
"""
import asyncio

import httpx
import pytest
import pytest_asyncio

from app.core.config import settings
from app.domain.models.chat_models import ChatRequest, ChatResponse
from app.infrastructure.clients.business_logic_client import BusinessLogicClient
from app.services.llm_service import LLMService


@pytest.fixture
def event_loop():
    """Provide an event loop for asyncio tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def business_logic_client():
    """Provide a BusinessLogicClient instance with a valid token."""
    client = BusinessLogicClient()
    token_renewed = await client.renew_token()
    if not token_renewed:
        pytest.skip("Failed to get token for backend API. Skipping test.")
    return client


@pytest_asyncio.fixture
async def access_token():
    """Get a valid access token for the backend API."""
    auth_credentials = {
        "email": settings.AUTH_EMAIL,
        "password": settings.AUTH_PASSWORD,
    }

    async with httpx.AsyncClient() as client:
        try:
            url = f"{settings.API_BASE_URL_DEV + '/api'}/login"
            response = await client.post(url, json=auth_credentials)
            response.raise_for_status()
            data = response.json()

            if "access_token" in data:
                return data["access_token"]
            else:
                pytest.skip("Failed to get access token. Skipping test.")
        except Exception as e:
            pytest.skip(f"Failed to get access token: {str(e)}. Skipping test.")


@pytest.fixture
def test_chat_request():
    """Provide a test ChatRequest instance."""
    return ChatRequest(
        message="Test message for the chatbot", session_id="test-session-123"
    )


@pytest.fixture
def test_chat_response():
    """Provide a test ChatResponse instance."""
    return ChatResponse(
        reply="This is a test response from the chatbot", session_id="test-session-123"
    )


@pytest.fixture
def llm_service():
    """Provide an LLMService instance."""
    return LLMService()
