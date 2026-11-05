# FullStyle Chatbot Tests

This directory contains tests for the FullStyle Chatbot application. This README provides a comprehensive guide to understanding, running, and maintaining the test suite.

## Test Structure

The tests are organized into the following directories:

```
tests/
├── __init__.py
├── conftest.py           # Common test fixtures
├── integration/          # Integration tests
│   ├── __init__.py
│   ├── test_backend_connection.py
│   ├── test_business_logic_client.py
│   └── test_llm_service.py
└── unit/                 # Unit tests
    ├── __init__.py
    ├── test_chat_message.py
    └── test_chat_session.py
```

## Test Types

### Unit Tests

These tests verify the behavior of individual components in isolation:

- **test_chat_message.py** - Tests for the ChatRequest and ChatResponse models
- **test_chat_session.py** - Tests for chat session management in LLMService

### Integration Tests

These tests verify that different components work together correctly:

- **test_backend_connection.py** - Tests connectivity to the FullStyle-Backend
- **test_business_logic_client.py** - Tests the BusinessLogicClient functionality
- **test_llm_service.py** - Tests the LLM service integration

## Running Tests

### Using the Test Runner Script (Recommended)

The easiest way to run tests is using the test runner script:

```powershell
# Windows PowerShell
.\run_tests.ps1

# Windows Command Prompt
run_tests.bat
```

This will present a menu with options to run different test suites.

### Using Pytest Directly

You can also run tests directly with pytest:

```bash
# Run all tests
python -m pytest

# Run unit tests only
python -m pytest tests/unit/

# Run integration tests only
python -m pytest tests/integration/

# Run a specific test file
python -m pytest tests/unit/test_chat_message.py
```

## Test Requirements

The tests require an active backend service. Make sure the FullStyle Backend is running before executing the integration tests.

### Starting the Backend

```powershell
cd c:\Users\holah\Documents\GitHub\FullStyle-Backend
docker-compose up -d
```

## Test Environment Variables

The tests use the same environment variables as the main application. Make sure your `.env` file is properly configured with:

- `GEMINI_API_KEY`: API key for Gemini LLM
- `API_BASE_URL_DEV`: The URL of the FullStyle Backend API
- `AUTH_EMAIL`: Email for authenticating with the backend
- `AUTH_PASSWORD`: Password for authenticating with the backend
- `MONGO_ATLAS_URI`:Mongo atlas connection string
- `MONGO_DATABASE_NAME`
- `MONGO_KB_COLLECTION_NAME`
- `ATLAS_VECTOR_SEARCH_INDEX_NAME`

## Test Fixtures

Common test fixtures are defined in `conftest.py`:

- **event_loop** - Provides an asyncio event loop for async tests
- **business_logic_client** - Provides a BusinessLogicClient instance with a valid token
- **access_token** - Gets a valid access token for the backend API
- **test_chat_request** - Provides a test ChatRequest instance
- **test_chat_response** - Provides a test ChatResponse instance
- **llm_service** - Provides an LLMService instance

## Troubleshooting

If you encounter connection issues between the chatbot and backend:

1. Make sure the backend is running:

   ```powershell
   cd c:\Users\holah\Documents\GitHub\FullStyle-Backend
   docker-compose ps
   ```

2. Test the connection directly:

   ```powershell
   python -m tests.manual.test_connection_script
   ```

3. Check the .env file in the chatbot directory for correct credentials.

4. Check backend logs for errors:
   ```powershell
   cd c:\Users\holah\Documents\GitHub\FullStyle-Backend
   docker-compose logs --tail 50
   ```
