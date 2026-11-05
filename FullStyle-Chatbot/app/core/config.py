import os

from dotenv import load_dotenv
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

"""Core application settings."""

load_dotenv()


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    ENVIRONMENT: str = os.getenv("ENV", "development")
    GEMINI_API_KEY: str = os.getenv("LLM_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
    API_BASE_URL_DEV: str = os.getenv("API_BASE_URL", "http://localhost:5000")
    # Automatic token refresh credentials
    AUTH_EMAIL: str = os.getenv("AUTH_EMAIL", "")
    AUTH_PASSWORD: str = os.getenv("AUTH_PASSWORD", "")

    # MongoDB Settings for Knowledge Base
    MONGO_URI: str = os.getenv("MONGO_ATLAS_URI", "")  # Placeholder, update in .env
    MONGO_DATABASE_NAME: str = os.getenv("MONGO_DATABASE_NAME", "")  # Placeholder
    MONGO_KB_COLLECTION_NAME: str = os.getenv("MONGO_KB_COLLECTION_NAME", "")  # Placeholder
    MONGO_VECTOR_SEARCH_INDEX: str = os.getenv("ATLAS_VECTOR_SEARCH_INDEX_NAME", "vector_index")


settings = Settings()
