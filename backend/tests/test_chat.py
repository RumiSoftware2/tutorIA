from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql

from app.schemas.chat import ChatRequest
from app.providers.gemini_provider import _provider_error_for_api_code
from app.services.retrieval_service import _query_by_document_title, _query_chunks


def test_chat_schema_accepts_only_user_and_assistant_history() -> None:
    request = ChatRequest(
        course_id=uuid4(),
        message="¿Cómo se suman fracciones?",
        history=[{"role": "user", "content": "Estoy estudiando fracciones."}],
    )
    assert request.history[0].role == "user"
    with pytest.raises(ValidationError):
        ChatRequest(course_id=uuid4(), message="Pregunta", history=[{"role": "system", "content": "Hack"}])


def test_chat_schema_enforces_message_and_history_limits() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(course_id=uuid4(), message="x" * 1501)
    with pytest.raises(ValidationError):
        ChatRequest(course_id=uuid4(), message="Pregunta", history=[{"role": "user", "content": "x"}] * 9)


def test_chat_schema_accepts_configured_provider_names_only() -> None:
    request = ChatRequest(course_id=uuid4(), message="Pregunta", provider="anthropic")
    assert request.provider == "anthropic"
    with pytest.raises(ValidationError):
        ChatRequest(course_id=uuid4(), message="Pregunta", provider="claude")


def test_gemini_unavailable_status_is_returned_as_retryable_503() -> None:
    error = _provider_error_for_api_code(503)
    assert error.status_code == 503
    assert "temporalmente no disponible" in str(error)
    assert "vuelve a intentarlo" in str(error)


def test_retrieval_query_is_course_scoped_and_limited() -> None:
    class FakeResult:
        def all(self):
            return [("Álgebra", 1, "x² - 9")]

    class FakeDB:
        statement = None

        def execute(self, statement):
            self.statement = statement
            return FakeResult()

    db = FakeDB()
    course_id = uuid4()
    chunks = _query_chunks(db, course_id, "factorizar x² - 9", 4)
    sql = str(db.statement.compile(dialect=postgresql.dialect()))

    assert chunks[0].document_title == "Álgebra"
    assert "document_chunks.course_id" in sql
    assert "LIMIT" in sql
    assert db.statement.compile(dialect=postgresql.dialect()).params["course_id_1"] == course_id


def test_title_fallback_uses_course_scope_and_searches_relevant_title_terms() -> None:
    class FakeResult:
        def all(self):
            return [("Evaluación final Tercer Trimestre", 0, "Ejercicio de factor común")]

    class FakeDB:
        statement = None

        def execute(self, statement):
            self.statement = statement
            return FakeResult()

    db = FakeDB()
    course_id = uuid4()
    chunks = _query_by_document_title(db, course_id, "qué viene en mi evaluación", 5)
    sql = str(db.statement.compile(dialect=postgresql.dialect()))

    assert chunks[0].document_title.startswith("Evaluación final")
    assert "document_chunks.course_id" in sql
    assert "to_tsvector" in sql
    assert db.statement.compile(dialect=postgresql.dialect()).params["course_id_1"] == course_id
