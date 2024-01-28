from __future__ import annotations

import datetime
from collections.abc import Sequence
from enum import Enum

from flask import current_app
from flask_login import UserMixin
from sqlalchemy import Boolean, Date, DateTime, Integer, String, event, extract
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from .extenstions import db
from .utils.storage import delete_blob_from_url


class OauthProvider(Enum):
    GOOGLE = "google"
    LINKEDIN = "linkedin"
    APPLE = "apple"


class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type = mapped_column(String)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __mapper_args__ = {"polymorphic_identity": "user", "polymorphic_on": type}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<User {self.email} | {self.type}>"

    @classmethod
    def delete_by_id(cls, id: int) -> None:
        if user := cls.get_by_id(id):
            db.session.delete(user)
            db.session.commit()

    @classmethod
    def get_by_id(cls, id: int) -> User | None:
        return db.session.scalar(db.select(cls).where(cls.id == id))

    @classmethod
    def get_by_email(cls, email: str) -> User | None:
        return db.session.scalar(db.select(cls).where(cls.email == email))

    @classmethod
    def get_all(cls) -> Sequence[User]:
        return db.session.scalars(db.select(cls)).all()


class UserOauth(User):
    oauth_provider: Mapped[OauthProvider] = mapped_column(
        SQLEnum(OauthProvider), nullable=True
    )

    __mapper_args__ = {
        "polymorphic_identity": "user_oauth",
    }


class UserRegular(User):
    password_hash: Mapped[str] = mapped_column(String, nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "user_regular",
    }

    @property
    def password(self) -> None:
        raise AttributeError("Password is not a readable attribute.")

    @password.setter
    def password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password, "scrypt")

    def verify_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)


class CourseGroup(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    link: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    picture_url: Mapped[str] = mapped_column(String, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<CourseGroup '{self.name}'>"

    def get_courses(self) -> Sequence[Course]:
        return Course.get_by_course_group(self)

    @staticmethod
    def get_all() -> Sequence[CourseGroup]:
        return db.session.scalars(db.select(CourseGroup)).all()

    @staticmethod
    def get_by_name(name: str) -> CourseGroup | None:
        return db.session.scalar(db.select(CourseGroup).where(CourseGroup.name == name))

    @staticmethod
    def get_by_id(id: int) -> CourseGroup | None:
        return db.session.scalar(db.select(CourseGroup).where(CourseGroup.id == id))

    @staticmethod
    def delete_by_id(id: int) -> None:
        if course_group := CourseGroup.get_by_id(id):
            try:
                delete_blob_from_url(course_group.picture_url)
            except Exception:
                current_app.logger.warning(
                    f"Failed to delete blob from URL {course_group.picture_url}"
                )
            db.session.delete(course_group)
            db.session.commit()
        else:
            raise ValueError(f"Course group with id {id} does not exist")

    @staticmethod
    def get_by_link(link: str) -> CourseGroup | None:
        return db.session.scalar(db.select(CourseGroup).where(CourseGroup.link == link))

    @staticmethod
    def get_courses_by_link(link: str) -> Sequence[Course]:
        course_group = CourseGroup.get_by_link(link)
        return Course.get_by_course_group(course_group)


class Course(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    link: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    picture_url: Mapped[str] = mapped_column(String, nullable=False)
    course_group_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey("course_group.id")
    )

    course_group: Mapped[CourseGroup] = relationship(CourseGroup, backref="courses")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return super().__repr__()

    @staticmethod
    def get_all() -> Sequence[Course]:
        return db.session.scalars(db.select(Course)).all()

    @staticmethod
    def get_by_id(id: int) -> Course | None:
        return db.session.scalar(db.select(Course).where(Course.id == id))

    @staticmethod
    def delete_by_id(id: int) -> None:
        if course := Course.get_by_id(id):
            try:
                delete_blob_from_url(course.picture_url)
            except Exception:
                current_app.logger.warning(
                    f"Failed to delete blob from URL {course.picture_url}"
                )
            db.session.delete(course)
            db.session.commit()
        else:
            raise ValueError(f"Course with id {id} does not exist")

    @staticmethod
    def get_by_course_group(
        course_group: CourseGroup | None = None,
    ) -> Sequence[Course]:
        if not course_group:
            return Course.get_all()
        return db.session.scalars(
            db.select(Course).where(Course.course_group == course_group)
        ).all()


class Teacher(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    bio: Mapped[str] = mapped_column(String, nullable=True)
    picture_url: Mapped[str] = mapped_column(String, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return super().__repr__()

    @staticmethod
    def get_all(max: int = 9999) -> Sequence[Teacher]:
        return db.session.scalars(db.select(Teacher).limit(max)).all()

    @staticmethod
    def get_by_id(id: int) -> Teacher | None:
        return db.session.scalar(db.select(Teacher).where(Teacher.id == id))

    @staticmethod
    def delete_by_id(id: int) -> None:
        if teacher := Teacher.get_by_id(id):
            try:
                delete_blob_from_url(teacher.picture_url)
            except Exception:
                current_app.logger.warning(
                    f"Failed to delete blob from URL {teacher.picture_url}"
                )
            db.session.delete(teacher)
            db.session.commit()
        else:
            raise ValueError(f"Teacher with id {id} does not exist")


class Staff(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    picture_url: Mapped[str] = mapped_column(String, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return super().__repr__()

    @staticmethod
    def get_all(max: int = 9999) -> Sequence[Staff]:
        return db.session.scalars(db.select(Staff).limit(max)).all()

    @staticmethod
    def get_by_id(id: int) -> Staff | None:
        return db.session.scalar(db.select(Staff).where(Staff.id == id))

    @staticmethod
    def delete_by_id(id: int) -> None:
        if staff := Staff.get_by_id(id):
            try:
                delete_blob_from_url(staff.picture_url)
            except Exception:
                current_app.logger.warning(
                    f"Failed to delete blob from URL {staff.picture_url}"
                )
            db.session.delete(staff)
            db.session.commit()
        else:
            raise ValueError(f"Staff with id {id} does not exist")


class EventType(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    color: Mapped[str] = mapped_column(String, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return super().__repr__()

    @staticmethod
    def get_by_name(name: str) -> EventType | None:
        event_type = db.session.scalar(
            db.select(EventType).where(EventType.name == name)
        )
        return event_type

    @staticmethod
    def get_by_id(id: int) -> EventType | None:
        return db.session.scalar(db.select(EventType).where(EventType.id == id))

    @staticmethod
    def populate():
        master_class = EventType(
            name="Мастер-класс",
            description="Мастер-классы по различным предметам",
            color="fuchsia-300",
        )
        toefl = EventType(
            name="TOEFL",
            description="Тестирование TOEFL",
            color="indigo-300",
        )
        course_start = EventType(
            name="Начало курса",
            description="Начало курса по различным предметам",
            color="emerald-300",
        )
        ielts = EventType(
            name="IELTS",
            description="Тестирование IELTS",
            color="rose-300",
        )
        db.session.add_all([master_class, toefl, course_start, ielts])
        db.session.commit()


class Event(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    event_type_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("event_type.id"))

    event_type = relationship(EventType, backref="events")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return super().__repr__()

    @property
    def date_string(self) -> str:
        day = self.date.day
        month_russian = {
            1: "января",
            2: "февраля",
            3: "марта",
            4: "апреля",
            5: "мая",
            6: "июня",
            7: "июля",
            8: "августа",
            9: "сентября",
            10: "октября",
            11: "ноября",
            12: "декабря",
        }
        month = month_russian[self.date.month]
        return f"{day} {month}"

    @staticmethod
    def get_all() -> Sequence[Event]:
        return db.session.scalars(db.select(Event)).all()

    @staticmethod
    def get_this_month() -> Sequence[Event]:
        return db.session.scalars(
            db.select(Event)
            .order_by(Event.date)
            .where(Event.date >= datetime.date.today().replace(day=1))
        ).all()

    @staticmethod
    def get_by_month(month: int, year: int) -> Sequence[Event]:
        return (
            db.session.query(Event)
            .filter(
                extract("month", Event.date) == month,
                extract("year", Event.date) == year,
            )
            .order_by(Event.date)
            .all()
        )

    @staticmethod
    def get_by_date(date: datetime.date) -> Sequence[Event]:
        return db.session.scalars(db.select(Event).where(Event.date == date)).all()

    @staticmethod
    def populate():
        event1 = Event(
            name="Мастер-класс по английскому языку",
            description="Мы проведем мастер-класс по английскому языку",
            date=datetime.date(2024, 1, 1),
            event_type=EventType.get_by_name("Мастер-класс"),
        )
        event2 = Event(
            name="Мастер-класс по математике",
            description="Мы проведем мастер-класс по математике",
            date=datetime.date(2024, 1, 15),
            event_type=EventType.get_by_name("Мастер-класс"),
        )
        event3 = Event(
            name="Мастер-класс по программированию",
            description="Мы проведем мастер-класс по программированию",
            date=datetime.date(2024, 1, 20),
            event_type=EventType.get_by_name("Мастер-класс"),
        )
        event4 = Event(
            name="Мастер-класс по физике",
            description="Мы проведем мастер-класс по физике",
            date=datetime.date(2024, 1, 25),
            event_type=EventType.get_by_name("Мастер-класс"),
        )
        event5 = Event(
            name="Мастер-класс по химии",
            description="Мы проведем мастер-класс по химии",
            date=datetime.date(2024, 1, 15),
            event_type=EventType.get_by_name("Мастер-класс"),
        )
        event6 = Event(
            name="IELTS",
            description="Мы проведем мастер-класс по биологии",
            date=datetime.date(2024, 1, 15),
            event_type=EventType.get_by_name("IELTS"),
        )
        event7 = Event(
            name="Тестирование TOEFL",
            description="Мы проведем тестирование TOEFL",
            date=datetime.date(2024, 1, 15),
            event_type=EventType.get_by_name("TOEFL"),
        )
        event8 = Event(
            name="Старт курса по географии",
            description="Мы начнем курс по географии",
            date=datetime.date(2024, 1, 15),
            event_type=EventType.get_by_name("Начало курса"),
        )
        db.session.add_all(
            [event1, event2, event3, event4, event5, event6, event7, event8]
        )
        db.session.commit()


class Feedback(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return super().__repr__()

    @staticmethod
    def get_all() -> Sequence[Feedback]:
        return db.session.scalars(db.select(Feedback)).all()

    @staticmethod
    def get_by_id(id: int) -> Feedback | None:
        return db.session.scalar(db.select(Feedback).where(Feedback.id == id))

    @staticmethod
    def delete_by_id(id: int) -> None:
        if feedback := Feedback.get_by_id(id):
            db.session.delete(feedback)
            db.session.commit()


# @event.listens_for(EventType.__table__, "after_create")  # type: ignore
# def populate_event_type(*args, **kwargs):
#     EventType.populate()


# @event.listens_for(Event.__table__, "after_create")  # type: ignore
# def populate_event(*args, **kwargs):
#     Event.populate()
