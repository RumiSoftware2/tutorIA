from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import require_teacher
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.schemas.document import DocumentResponse
from app.services import course_service
from app.services.document_converter import (
    DocumentConversionError,
    DocumentInputError,
    DocumentTooLargeError,
    NoExtractableTextError,
    UnsupportedDocumentError,
)
from app.services.document_service import CourseNotFoundError, delete_document, list_course_documents, process_and_store_document

course_documents_router = APIRouter(prefix="/courses", tags=["documents"])
documents_router = APIRouter(prefix="/documents", tags=["documents"])


def _document_input_error(error: DocumentInputError) -> HTTPException:
    if isinstance(error, DocumentTooLargeError):
        return HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(error))
    if isinstance(error, UnsupportedDocumentError):
        return HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(error))
    if isinstance(error, NoExtractableTextError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error))
    if isinstance(error, DocumentConversionError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error))
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No se pudo procesar el documento.")


@course_documents_router.get(
    "/{course_id}/documents",
    response_model=list[DocumentResponse],
    dependencies=[Depends(require_teacher)],
)
def get_course_documents(course_id: UUID, db: Session = Depends(get_db)) -> list[DocumentResponse]:
    try:
        if course_service.get_course(db, course_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curso no encontrado.")
        return list_course_documents(db, course_id)
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudieron consultar los documentos.",
        ) from None


@course_documents_router.post(
    "/{course_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_teacher)],
)
def upload_course_document(
    course_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> DocumentResponse:
    max_file_bytes = settings.upload_max_mb * 1024 * 1024
    try:
        file_bytes = file.file.read(max_file_bytes + 1)
        return process_and_store_document(
            db,
            course_id=course_id,
            filename=file.filename,
            file_bytes=file_bytes,
            max_file_bytes=max_file_bytes,
            max_extracted_chars=settings.max_extracted_chars,
            chunk_size=settings.chunk_size_chars,
            chunk_overlap=settings.chunk_overlap_chars,
        )
    except CourseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curso no encontrado.") from None
    except DocumentInputError as error:
        raise _document_input_error(error) from None
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo guardar el documento. Inténtalo de nuevo.",
        ) from None


@documents_router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_teacher)],
)
def remove_document(document_id: UUID, db: Session = Depends(get_db)) -> None:
    try:
        removed = delete_document(db, document_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo eliminar el documento.",
        ) from None
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")
