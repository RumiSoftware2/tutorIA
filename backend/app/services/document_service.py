import re
import uuid
from pathlib import PurePosixPath

from sqlalchemy import func, insert, select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.document_converter import MIME_TYPES, convert_to_markdown
from app.services.text_chunker import split_into_chunks


class CourseNotFoundError(LookupError):
    pass


def _safe_filename(filename: str | None, extension: str) -> str:
    basename = (filename or f"documento.{extension}").replace("\\", "/").rsplit("/", 1)[-1]
    basename = re.sub(r"[\x00-\x1f\x7f]", "", basename).strip()
    return (basename or f"documento.{extension}")[:255]


def process_and_store_document(
    db: Session,
    *,
    course_id: uuid.UUID,
    filename: str | None,
    file_bytes: bytes,
    max_file_bytes: int,
    max_extracted_chars: int,
    chunk_size: int,
    chunk_overlap: int,
) -> Document:
    if db.get(Course, course_id) is None:
        raise CourseNotFoundError

    safe_filename = _safe_filename(filename, "pdf")
    extension = PurePosixPath(safe_filename).suffix.lower().lstrip(".")
    markdown = convert_to_markdown(
        file_bytes,
        extension,
        filename=safe_filename,
        max_bytes=max_file_bytes,
        max_extracted_chars=max_extracted_chars,
    )
    chunks = split_into_chunks(markdown, chunk_size=chunk_size, overlap=chunk_overlap)
    if not chunks:
        raise ValueError("El documento no produjo fragmentos con contenido.")

    title = PurePosixPath(safe_filename).stem[:255] or "Material de estudio"
    document = Document(
        course_id=course_id,
        title=title,
        original_filename=safe_filename,
        file_extension=extension,
        mime_type=MIME_TYPES[extension],
        file_size_bytes=len(file_bytes),
        status="ready",
        chunk_count=len(chunks),
    )

    try:
        db.add(document)
        db.flush()
        chunk_rows = [
            {
                "id": uuid.uuid4(),
                "document_id": document.id,
                "course_id": course_id,
                "chunk_index": index,
                "content": content,
                "search_vector": func.to_tsvector("spanish", content),
            }
            for index, content in enumerate(chunks)
        ]
        db.execute(insert(DocumentChunk).values(chunk_rows))
        db.commit()
        db.refresh(document)
        return document
    except Exception:
        db.rollback()
        raise


def list_course_documents(db: Session, course_id: uuid.UUID) -> list[Document]:
    statement = (
        select(Document)
        .where(Document.course_id == course_id)
        .order_by(Document.created_at.desc())
    )
    return list(db.scalars(statement).all())


def delete_document(db: Session, document_id: uuid.UUID) -> bool:
    document = db.get(Document, document_id)
    if document is None:
        return False
    try:
        db.delete(document)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return True
