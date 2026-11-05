"""
Integration tests for the LLM Service.
These tests verify that the LLM service can properly process chat inputs.
"""
import pytest

from app.services.llm_service import LLMService


@pytest.mark.asyncio
async def test_llm_service_initialization():
    """Test that we can initialize the LLM service."""
    # Create the LLM service
    llm_service = LLMService()

    # LLM service should be initialized with a model
    assert llm_service is not None, "LLM service is None"
    assert llm_service.agent_executor is not None, "Agent executor is None"


@pytest.mark.asyncio
async def test_llm_service_worker_query():
    """Test that we can query the LLM service about workers."""
    # Create the LLM service
    llm_service = LLMService()

    # Define a session ID for testing
    session_id = "test-session-123"
    # Create a test query about workers
    user_message_content = "Hay algún trabajador llamado Pedro?"

    # Process the query
    response = await llm_service.generate_text_with_agent(
        user_message_content, session_id
    )

    # Check that we got a non-empty response
    assert response is not None, "LLM service response is None"
    assert len(response) > 0, "LLM service response is empty"

    # Response should contain "Pedro" if a worker with that name exists
    # or should indicate no worker was found
    assert ("Pedro" in response) or (
        "no encontré" in response.lower()
    ), "Response doesn't mention worker"


@pytest.mark.asyncio
async def test_llm_service_services_query():
    """Test that we can query the LLM service about services."""
    # Create the LLM service
    llm_service = LLMService()

    # Define a session ID for testing
    session_id = "test-session-124"

    # Create a test query about services
    user_message_content = "¿Qué servicios ofrecen?"

    # Process the query
    response = await llm_service.generate_text_with_agent(
        user_message_content, session_id
    )

    # Check that we got a non-empty response
    assert response is not None, "LLM service response is None"
    assert len(response) > 0, "LLM service response is empty"

    # Response should mention "servicios" or be in Spanish
    assert ("servicio" in response.lower()) or (
        "ofrecemos" in response.lower()
    ), "Response doesn't mention services"
