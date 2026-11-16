import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.providers.base import TutorProviderError
from app.providers.fallback import build_tutor_provider
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.tutor_service import CourseUnavailableError, answer_course_question

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ChatResponse:
    if len(request.message) > settings.max_chat_message_chars:
        raise HTTPException(status_code=422, detail="La pregunta excede la longitud máxima permitida.")
    if len(request.history) > settings.max_history_messages:
        raise HTTPException(status_code=422, detail="El historial excede la cantidad máxima permitida.")
    if not settings.gemini_api_key:
        raise HTTPException(status_code=503, detail="El tutor no está configurado. Añade GEMINI_API_KEY al backend.")
    try:
        provider = build_tutor_provider(settings)
        answer, sources = answer_course_question(
            db, settings, provider,
            course_id=request.course_id,
            message=request.message,
            history=request.history,
        )
        logger.info("Chat respondido por proveedor=%s.", provider.provider_used)
    except CourseUnavailableError:
        raise HTTPException(status_code=404, detail="Curso activo no encontrado.") from None
    except TutorProviderError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from None
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="No se pudo consultar la información del curso.") from None
    return ChatResponse(answer=answer, sources=sources)
