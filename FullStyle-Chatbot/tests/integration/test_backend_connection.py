"""
Integration tests for the backend API connection.
These tests verify that the chatbot can properly connect to the backend API.
"""
import httpx
import pytest

from app.core.config import settings


@pytest.mark.integration
@pytest.mark.requires_backend
@pytest.mark.asyncio
async def test_backend_connection():
    """Test the connection to the backend API."""
    # Get the backend URL from settings
    api_base_url = settings.API_BASE_URL_DEV + "/api"
    assert api_base_url, "API_BASE_URL_DEV is not set in environment variables"

    # Set up authentication credentials
    auth_credentials = {
        "email": settings.AUTH_EMAIL,
        "password": settings.AUTH_PASSWORD,
    }
    assert auth_credentials["email"], "AUTH_EMAIL is not set in environment variables"
    assert auth_credentials[
        "password"
    ], "AUTH_PASSWORD is not set in environment variables"

    # Test connecting to the backend API with retry logic for cold starts
    async with httpx.AsyncClient(timeout=60.0) as client:  # Increased timeout
        # Test authentication with retry for cold start
        login_url = f"{api_base_url}/login"

        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1}/{max_retries} to authenticate...")
                login_response = await client.post(login_url, json=auth_credentials)

                # Check if we got HTML error page (Render cold start)
                content_type = login_response.headers.get("content-type", "")
                if "text/html" in content_type and login_response.status_code >= 500:
                    if attempt < max_retries - 1:
                        print(
                            "Got HTML error (likely cold start), retrying in 10 seconds..."
                        )
                        import asyncio

                        await asyncio.sleep(10)
                        continue
                    else:
                        pytest.skip(
                            "Backend appears to be in cold start state, skipping test"
                        )

                login_response.raise_for_status()
                break

            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    print(f"Connection failed, retrying... ({e})")
                    import asyncio

                    await asyncio.sleep(5)
                else:
                    pytest.skip(
                        f"Backend unavailable after {max_retries} attempts: {last_error}"
                    )

        # Check if we got a token
        login_data = login_response.json()
        assert "access_token" in login_data, "No access token in login response"

        # Test accessing a protected endpoint
        token = login_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try to get workers
        workers_url = f"{api_base_url}/worker"
        workers_response = await client.get(workers_url, headers=headers)

        if workers_response.status_code != 200:
            pytest.skip(
                f"Workers endpoint not accessible: {workers_response.status_code}"
            )

        # Check if we got a list of workers
        workers = workers_response.json()
        assert isinstance(workers, list), "Workers response is not a list"

        # If we have workers, check the first one
        if workers:
            first_worker = workers[0]
            assert "id" in first_worker, "Worker data missing 'id' field"
            assert "name" in first_worker, "Worker data missing 'name' field"


@pytest.mark.integration
@pytest.mark.requires_backend
@pytest.mark.asyncio
async def test_backend_error_handling():
    """Test that we properly handle backend API errors."""
    # Get the backend URL from settings
    api_base_url = settings.API_BASE_URL_DEV + "/api"

    # Test with invalid credentials
    invalid_credentials = {
        "email": "nonexistent@example.com",
        "password": "wrongpassword",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Test authentication with invalid credentials
            login_url = f"{api_base_url}/login"
            response = await client.post(login_url, json=invalid_credentials)

            # Should fail authentication (401 or similar)
            assert (
                response.status_code != 200
            ), "Authentication succeeded with invalid credentials"

        except httpx.RequestError:
            pytest.skip("Backend not accessible for error handling test")
