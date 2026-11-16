from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def normalize_topics(topics: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for topic in topics:
        clean_topic = topic.strip()
        if not clean_topic:
            raise ValueError("Los temas no pueden estar vacíos.")
        key = clean_topic.casefold()
        if key not in seen:
            normalized.append(clean_topic)
            seen.add(key)
    return normalized


class CourseCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=150)
    description: str = Field(min_length=1, max_length=5000)
    grade_level: str | None = Field(default=None, max_length=60)
    subject: str = Field(default="Matemáticas", min_length=1, max_length=80)
    topics: list[str] = Field(default_factory=list, max_length=30)

    @field_validator("topics")
    @classmethod
    def clean_topics(cls, topics: list[str]) -> list[str]:
        if any(len(topic.strip()) > 80 for topic in topics):
            raise ValueError("Cada tema debe tener como máximo 80 caracteres.")
        return normalize_topics(topics)


class CourseUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, min_length=1, max_length=5000)
    grade_level: str | None = Field(default=None, max_length=60)
    subject: str | None = Field(default=None, min_length=1, max_length=80)
    topics: list[str] | None = Field(default=None, max_length=30)

    @field_validator("topics")
    @classmethod
    def clean_topics(cls, topics: list[str] | None) -> list[str] | None:
        if topics is None:
            return None
        if any(len(topic.strip()) > 80 for topic in topics):
            raise ValueError("Cada tema debe tener como máximo 80 caracteres.")
        return normalize_topics(topics)

    @model_validator(mode="after")
    def reject_null_required_fields(self) -> "CourseUpdate":
        for field in ("title", "description", "subject", "topics"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} no puede ser nulo.")
        return self


class CourseStatusUpdate(BaseModel):
    is_active: bool


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    grade_level: str | None
    subject: str
    topics: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
