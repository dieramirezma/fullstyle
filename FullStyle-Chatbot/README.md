# FullStyle-Chatbot

Chatbot service made with Python (FastAPI) and using LangChain for integrating FullStyle application's endpoints via an API gateway.

## Overview

The FullStyle Chatbot is an intelligent assistant for booking appointments at barbershops and hair salons. It integrates with the FullStyle Backend API to provide information about:

- Available services
- Stylists and barbers
- Shop locations
- Available appointment times
- Booking appointments

## Project Structure

```
FullStyle-Chatbot/
├── app/                       # Main application code
│   ├── api/                   # API endpoints
│   ├── core/                  # Core functionality (config, etc.)
│   ├── domain/                # Domain models and business logic
│   ├── infrastructure/        # External services and clients
│   └── services/              # Application services
├── tests/                     # Tests
│   ├── integration/           # Integration tests
│   └── unit/                  # Unit tests
└── docker-compose.yml         # Docker configuration
```

## Setup

### Prerequisites

- Python 3.9+
- Docker (optional)
- FullStyle Backend running

### Installation

1. Clone the repository

```bash
git clone https://github.com/YourOrganization/FullStyle-Chatbot.git
cd FullStyle-Chatbot
```

2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. For development, install development dependencies

```bash
pip install -r requirements-dev.txt
```

5. Create a `.env` file with the following variables:

```
GEMINI_API_KEY
API_BASE_URL_DEV
AUTH_EMAIL
AUTH_PASSWORD
```

## Running the Chatbot

### Local Development

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### Using Docker

```bash
docker-compose up --build
```

## Testing

### Running Tests

You can run tests using the test runner script:

```bash
# On Windows PowerShell
.\run_tests.ps1

# On Windows Command Prompt
run_tests.bat
```

Or run tests directly with pytest:

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/
```
