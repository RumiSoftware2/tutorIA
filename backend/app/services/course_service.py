from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.course import Course


def list_active_courses(db: Session) -> list[Course]:
    statement = select(Course).where(Course.is_active.is_(True)).order_by(Course.created_at.desc())
    return list(db.scalars(statement).all())


def list_all_courses(db: Session) -> list[Course]:
    return list(db.scalars(select(Course).order_by(Course.created_at.desc())).all())


def get_active_course(db: Session, course_id: UUID) -> Course | None:
    statement = select(Course).where(Course.id == course_id, Course.is_active.is_(True))
    return db.scalar(statement)


def create_course(db: Session, course_data: dict) -> Course:
    course = Course(**course_data)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def update_course(db: Session, course_id: UUID, changes: dict) -> Course | None:
    course = db.get(Course, course_id)
    if course is None:
        return None
    for field, value in changes.items():
        setattr(course, field, value)
    db.commit()
    db.refresh(course)
    return course


def set_course_active(db: Session, course_id: UUID, is_active: bool) -> Course | None:
    course = db.get(Course, course_id)
    if course is None:
        return None
    course.is_active = is_active
    db.commit()
    db.refresh(course)
    return course
