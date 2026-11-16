import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    grade_level: Mapped[str | None] = mapped_column(String(60))
    subject: Mapped[str] = mapped_column(String(80), nullable=False, default="Matemáticas", server_default="Matemáticas")
    topics: Mapped[list[str]] = mapped_column(JSON().with_variant(JSONB(), "postgresql"), nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    documents: Mapped[list["Document"]] = relationship(
        back_populates="course", cascade="all, delete-orphan", passive_deletes=True
    )
