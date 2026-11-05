"""
Integration tests for the BusinessLogicClient class.
Tests the connection with the FullStyle backend API.
"""
import pytest

from app.infrastructure.clients.business_logic_client import BusinessLogicClient


@pytest.mark.integration
@pytest.mark.requires_backend
@pytest.mark.asyncio
async def test_login_and_token():
    """Test that we can authenticate with the backend API and get a valid token."""
    client = BusinessLogicClient()

    # Test token renewal (login)
    token_renewed = await client.renew_token()
    assert token_renewed is True, "Failed to renew token (login failed)"

    # Check that we have a valid Authorization header
    assert client.headers.get("Authorization", "").startswith(
        "Bearer "
    ), "Authorization header does not contain a Bearer token"


@pytest.mark.integration
@pytest.mark.requires_backend
@pytest.mark.asyncio
async def test_get_workers():
    """Test that we can fetch workers from the backend API."""
    client = BusinessLogicClient()

    # Ensure we have a token
    await client.renew_token()

    # Test fetching workers
    workers = await client.get_workers()
    assert workers is not None, "Failed to fetch workers"
    assert isinstance(workers, list), "Workers data is not a list"

    # If there are workers, verify the structure of the first worker
    if workers:
        worker = workers[0]
        assert "id" in worker, "Worker data missing 'id' field"
        assert "name" in worker, "Worker data missing 'name' field"


@pytest.mark.integration
@pytest.mark.requires_backend
@pytest.mark.asyncio
async def test_get_services():
    """Test that we can fetch services from the backend API."""
    client = BusinessLogicClient()

    # Ensure we have a token
    await client.renew_token()

    # Test fetching services
    services = await client.get_services()
    assert services is not None, "Failed to fetch services"
    assert isinstance(services, list), "Services data is not a list"


@pytest.mark.integration
@pytest.mark.requires_backend
@pytest.mark.asyncio
async def test_get_sites():
    """Test that we can fetch sites from the backend API."""
    client = BusinessLogicClient()

    # Ensure we have a token
    await client.renew_token()

    # Test fetching sites
    sites = await client.get_sites()
    assert sites is not None, "Failed to fetch sites"
    assert isinstance(sites, list), "Sites data is not a list"
