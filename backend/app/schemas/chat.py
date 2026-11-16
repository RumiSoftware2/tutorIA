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


class ChatSource(BaseModel):
    document_title: str
    chunk_index: int


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]
