from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        ..., min_length=1, max_length=2000, description="The message from the user."
    )
    session_id: str | None = Field(
        None,
        max_length=120,
        pattern=r"^[A-Za-z0-9._:-]+$",
        description="Optional session ID for conversation history.",
    )
    # user_id: str | None = Field(None, description="user ID for tracking user-specific data and booking appointments.")


class ChatResponse(BaseModel):
    reply: str = Field(..., description="The chatbot's reply.")
    session_id: str | None = Field(None, description="Session ID, passed through or generated.")
    debug_info: dict | None = Field(None, description="Optional debug information.")
    error: str | None = Field(None, description="Error message if something went wrong.")
