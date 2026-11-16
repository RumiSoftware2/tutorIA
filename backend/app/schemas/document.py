from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    title: str
    original_filename: str
    file_extension: str
    mime_type: str
    file_size_bytes: int
    status: str
    chunk_count: int
    error_message: str | None
    created_at: datetime
