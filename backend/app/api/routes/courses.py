from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import require_teacher
from app.core.database import get_db
from app.schemas.course import CourseCreate, CourseResponse, CourseStatusUpdate, CourseUpdate
from app.services import course_service

router = APIRouter(prefix="/courses", tags=["courses"])


def database_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="No se pudo completar la operación con la base de datos.",
    )


@router.get("", response_model=list[CourseResponse])
def get_public_courses(db: Session = Depends(get_db)) -> list[CourseResponse]:
    try:
        return course_service.list_active_courses(db)
    except SQLAlchemyError:
        raise database_unavailable() from None


@router.get("/manage", response_model=list[CourseResponse], dependencies=[Depends(require_teacher)])
def get_teacher_courses(db: Session = Depends(get_db)) -> list[CourseResponse]:
    try:
        return course_service.list_all_courses(db)
    except SQLAlchemyError:
        raise database_unavailable() from None


@router.get("/{course_id}", response_model=CourseResponse)
def get_public_course(course_id: UUID, db: Session = Depends(get_db)) -> CourseResponse:
    try:
        course = course_service.get_active_course(db, course_id)
    except SQLAlchemyError:
        raise database_unavailable() from None
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curso no encontrado.")
    return course


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_teacher)])
def create_new_course(request: CourseCreate, db: Session = Depends(get_db)) -> CourseResponse:
    try:
        return course_service.create_course(db, request.model_dump())
    except SQLAlchemyError:
        db.rollback()
        raise database_unavailable() from None


@router.patch("/{course_id}", response_model=CourseResponse, dependencies=[Depends(require_teacher)])
def edit_course(course_id: UUID, request: CourseUpdate, db: Session = Depends(get_db)) -> CourseResponse:
    changes = request.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Envía al menos un campo para actualizar.")
    try:
        course = course_service.update_course(db, course_id, changes)
    except SQLAlchemyError:
        db.rollback()
        raise database_unavailable() from None
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curso no encontrado.")
    return course


@router.patch("/{course_id}/status", response_model=CourseResponse, dependencies=[Depends(require_teacher)])
def change_course_status(
    course_id: UUID,
    request: CourseStatusUpdate,
    db: Session = Depends(get_db),
) -> CourseResponse:
    try:
        course = course_service.set_course_active(db, course_id, request.is_active)
    except SQLAlchemyError:
        db.rollback()
        raise database_unavailable() from None
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curso no encontrado.")
    return course
