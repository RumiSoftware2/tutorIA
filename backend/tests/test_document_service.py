import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import insert
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import SQLAlchemyError

from app.models.course import Course
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services import document_service
from app.services.document_service import CourseNotFoundError, process_and_store_document


class FakeSession:
    def __init__(self, course_exists: bool = True, fail_on_execute: bool = False) -> None:
        self.course_exists = course_exists
        self.fail_on_execute = fail_on_execute
        self.document: Document | None = None
        self.statement = None
        self.committed = False
        self.rolled_back = False

    def get(self, model: type, _identifier: uuid.UUID) -> object | None:
        if model is Course and self.course_exists:
            return object()
        return None

    def add(self, value: Document) -> None:
        self.document = value

    def flush(self) -> None:
        assert self.document is not None
        self.document.id = uuid.uuid4()

    def execute(self, statement: object) -> None:
        if self.fail_on_execute:
            raise SQLAlchemyError("database failure")
        self.statement = statement

    def commit(self) -> None:
        self.committed = True

    def refresh(self, value: Document) -> None:
        value.created_at = datetime.now(timezone.utc)

    def rollback(self) -> None:
        self.rolled_back = True


def _run_service(db: FakeSession) -> Document:
    return process_and_store_document(
        db,  # type: ignore[arg-type]
        course_id=uuid.uuid4(),
        filename=r"C:\uploads\algebra.pdf",
        file_bytes=b"%PDF-fake",
        max_file_bytes=1024,
        max_extracted_chars=1000,
        chunk_size=25,
        chunk_overlap=5,
    )


def test_document_service_commits_metadata_and_spanish_search_vectors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(document_service, "convert_to_markdown", lambda *_args, **_kwargs: "Primera idea. Segunda idea.")
    db = FakeSession()

    document = _run_service(db)

    assert db.committed is True
    assert db.rolled_back is False
    assert document.status == "ready"
    assert document.original_filename == "algebra.pdf"
    assert document.mime_type == "application/pdf"
    assert document.chunk_count > 0
    assert db.statement is not None
    assert isinstance(db.statement, type(insert(DocumentChunk).values([])))
    compiled = str(db.statement.compile(dialect=postgresql.dialect()))
    compiled_statement = db.statement.compile(dialect=postgresql.dialect())
    assert "to_tsvector" in compiled
    assert "spanish" in compiled_statement.params.values()


def test_document_service_never_stores_a_document_without_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(document_service, "convert_to_markdown", lambda *_args, **_kwargs: "texto")
    db = FakeSession(fail_on_execute=True)

    with pytest.raises(SQLAlchemyError):
        _run_service(db)

    assert db.committed is False
    assert db.rolled_back is True


def test_document_service_checks_course_before_conversion(monkeypatch: pytest.MonkeyPatch) -> None:
    conversion_called = False

    def convert(*_args, **_kwargs):
        nonlocal conversion_called
        conversion_called = True
        return "texto"

    monkeypatch.setattr(document_service, "convert_to_markdown", convert)
    db = FakeSession(course_exists=False)

    with pytest.raises(CourseNotFoundError):
        _run_service(db)

    assert conversion_called is False
