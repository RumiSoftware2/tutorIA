from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1_500)


class ChatRequest(BaseModel):
    course_id: UUID
    message: str = Field(min_length=1, max_length=1_500)
    history: list[ChatHistoryMessage] = Field(default_factory=list, max_length=8)
    provider: Literal["openai", "anthropic", "groq", "gemini"] | None = None


class ChatSource(BaseModel):
    document_title: str
    chunk_index: int


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]
    provider_used: Literal["openai", "anthropic", "groq", "gemini"] | None = None


class ProviderAvailability(BaseModel):
    provider: Literal["openai", "anthropic", "groq", "gemini"]
    display_name: str
    status: Literal["configured", "available", "requires_configuration", "temporarily_unavailable"]
    message: str
    availability_verified: bool = False
