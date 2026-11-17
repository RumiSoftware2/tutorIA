import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings, get_settings
from app.core.database import create_session
from app.providers.base import TutorProviderError
from app.providers.fallback import TutorProviderManager
from app.schemas.chat import ChatRequest, ChatResponse, ProviderAvailability
from app.services.tutor_service import CourseUnavailableError, PreparedCourseQuestion, prepare_course_question

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


def get_provider_manager(request: Request) -> TutorProviderManager:
    manager = getattr(request.app.state, "provider_manager", None)
    if manager is None:
        raise HTTPException(status_code=503, detail="El servicio del tutor no está inicializado.")
    return manager


def _prepare(request: ChatRequest, settings: Settings) -> PreparedCourseQuestion:
    db = create_session()
    try:
        return prepare_course_question(db, settings, course_id=request.course_id,
                                       message=request.message, history=request.history)
    finally:
        db.close()


@router.get("/providers", response_model=list[ProviderAvailability])
def provider_availability(manager: TutorProviderManager = Depends(get_provider_manager)):
    return manager.availability()


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, settings: Settings = Depends(get_settings),
               manager: TutorProviderManager = Depends(get_provider_manager)) -> ChatResponse:
    if len(request.message) > settings.max_chat_message_chars:
        raise HTTPException(status_code=422, detail="La pregunta excede la longitud máxima permitida.")
    if len(request.history) > settings.max_history_messages:
        raise HTTPException(status_code=422, detail="El historial excede la cantidad máxima permitida.")
    if request.provider and request.provider not in manager.providers:
        raise HTTPException(status_code=409, detail="El proveedor seleccionado requiere configuración en el backend.")
    try:
        prepared = await run_in_threadpool(_prepare, request, settings)
        if prepared.immediate_answer is not None:
            return ChatResponse(answer=prepared.immediate_answer, sources=prepared.sources)
        answer, provider_used = await manager.generate(system_instruction=prepared.system_instruction,
                                                       contents=prepared.contents, preferred=request.provider)
        return ChatResponse(answer=answer, sources=prepared.sources, provider_used=provider_used)
    except CourseUnavailableError:
        raise HTTPException(status_code=404, detail="Curso activo no encontrado.") from None
    except TutorProviderError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from None
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="No se pudo consultar la información del curso.") from None
