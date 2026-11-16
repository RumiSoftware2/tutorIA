from dataclasses import dataclass
import re
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk


@dataclass(frozen=True)
class RetrievedChunk:
    document_title: str
    chunk_index: int
    content: str


def _query_chunks(db: Session, course_id: UUID, query: str, limit: int) -> list[RetrievedChunk]:
    tsquery = func.websearch_to_tsquery("spanish", query)
    rank = func.ts_rank(DocumentChunk.search_vector, tsquery)
    statement = (
        select(Document.title, DocumentChunk.chunk_index, DocumentChunk.content)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            DocumentChunk.course_id == course_id,
            DocumentChunk.search_vector.op("@@")(tsquery),
        )
        .order_by(rank.desc())
        .limit(limit)
    )
    return [RetrievedChunk(title, index, content) for title, index, content in db.execute(statement).all()]


def _query_by_document_title(db: Session, course_id: UUID, query: str, limit: int) -> list[RetrievedChunk]:
    """Use title terms as a fallback when a question names a material by its title."""
    ignored = {"donde", "cuando", "cuales", "cual", "debo", "deben", "puedo", "pueden", "quiero", "saber", "explica", "explicame", "muestra", "dime", "tema", "temas", "documento", "archivo"}
    terms = [term for term in re.findall(r"[\wáéíóúüñ]+", query.lower()) if len(term) >= 5 and term not in ignored]
    if not terms:
        return []
    title_vector = func.to_tsvector("spanish", Document.title)
    title_matches = [
        title_vector.op("@@")(func.plainto_tsquery("spanish", term))
        for term in terms
    ]
    statement = (
        select(Document.title, DocumentChunk.chunk_index, DocumentChunk.content)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(DocumentChunk.course_id == course_id, or_(*title_matches))
        .order_by(Document.created_at.desc(), DocumentChunk.chunk_index.asc())
        .limit(limit)
    )
    return [RetrievedChunk(title, index, content) for title, index, content in db.execute(statement).all()]


def retrieve_course_chunks(
    db: Session, course_id: UUID, question: str, *, top_k: int = 5, max_context_chars: int = 8_000
) -> list[RetrievedChunk]:
    """Retrieve relevant chunks, strictly scoped to one course and context budget."""
    query = question.strip()
    if not query:
        return []
    results = _query_chunks(db, course_id, query, top_k)
    if not results:
        results = _query_by_document_title(db, course_id, query, top_k)
    # PostgreSQL text search drops many mathematical operators. Retry using literal
    # expression fragments, retaining the mandatory course filter and top-K cap.
    if not results and any(char in query for char in "+-*/=^()√<>≤≥"):
        results = []
        for term in (query, *[part for part in query.split() if any(c.isdigit() for c in part)]):
            if not term:
                continue
            statement = (
                select(Document.title, DocumentChunk.chunk_index, DocumentChunk.content)
                .join(Document, Document.id == DocumentChunk.document_id)
                .where(DocumentChunk.course_id == course_id, DocumentChunk.content.icontains(term, autoescape=True))
                .limit(top_k)
            )
            results = [RetrievedChunk(title, index, content) for title, index, content in db.execute(statement).all()]
            if results:
                break
    output: list[RetrievedChunk] = []
    used = 0
    for chunk in results:
        remaining = max_context_chars - used
        if remaining <= 0:
            break
        content = chunk.content[:remaining]
        output.append(RetrievedChunk(chunk.document_title, chunk.chunk_index, content))
        used += len(content)
    return output
