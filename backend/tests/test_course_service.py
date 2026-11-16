import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models.course import Course
from app.schemas.course import CourseCreate, CourseUpdate
from app.services.course_service import (
    create_course,
    list_active_courses,
    list_all_courses,
    set_course_active,
    update_course,
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite+pysqlite://")
    Course.__table__.create(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def test_course_schema_cleans_and_deduplicates_topics() -> None:
    course = CourseCreate(
        title="  Álgebra  ",
        description="  Temas iniciales.  ",
        topics=["Factor común", " factor COMÚN ", "Polinomios"],
    )

    assert course.title == "Álgebra"
    assert course.topics == ["Factor común", "Polinomios"]


def test_course_schema_rejects_blank_title() -> None:
    with pytest.raises(ValidationError):
        CourseCreate(title="   ", description="Descripción")


def test_teacher_course_crud_and_active_filter(db_session: Session) -> None:
    data = CourseCreate(
        title="Aritmética",
        description="Operaciones básicas",
        topics=["Fracciones"],
    )
    course = create_course(db_session, data.model_dump())

    assert course.id is not None
    assert len(list_active_courses(db_session)) == 1
    assert len(list_all_courses(db_session)) == 1

    updated = update_course(db_session, course.id, {"description": "Fracciones y razones"})
    assert updated is not None
    assert updated.description == "Fracciones y razones"

    inactive = set_course_active(db_session, course.id, False)
    assert inactive is not None
    assert inactive.is_active is False
    assert list_active_courses(db_session) == []
    assert len(list_all_courses(db_session)) == 1
