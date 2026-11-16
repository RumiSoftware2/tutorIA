from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import configure_mappers

from app.models import Base
from app.models.document_chunk import DocumentChunk


def test_initial_models_have_expected_tables_and_search_index() -> None:
    configure_mappers()
    assert set(Base.metadata.tables) == {"courses", "documents", "document_chunks"}
    assert "uq_document_chunks_document_index" in {
        constraint.name for constraint in Base.metadata.tables["document_chunks"].constraints
    }
    assert any(index.name == "ix_document_chunks_search_vector" for index in DocumentChunk.__table__.indexes)


def test_search_vector_uses_postgresql_type() -> None:
    compiled = DocumentChunk.__table__.c.search_vector.type.compile(dialect=postgresql.dialect())

    assert compiled == "TSVECTOR"
