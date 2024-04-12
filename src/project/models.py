from __future__ import annotations

import datetime
from collections.abc import Sequence
from enum import Enum

from flask import current_app
from flask_login import UserMixin
from flask_sqlalchemy.pagination import Pagination
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Integer,
    String,
    extract,
    func,
    inspect,
    select,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import (
    Mapped,
    MappedAsDataclass,
    joinedload,
    mapped_column,
    relationship,
)
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
        if user := cls.get_by_id(int(id)):
            db.session.delete(user)
            db.session.commit()

    @classmethod
    def get_by_id(cls, id: int) -> User | None:
        return db.session.scalar(select(cls).where(cls.id == int(id)))

    @classmethod
    def get_by_email(cls, email: str) -> User | None:
        return db.session.scalar(select(cls).where(cls.email == email))

    @classmethod
    def get_all(cls) -> Sequence[User]:
        return db.session.scalars(select(cls)).all()


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


def to_dict(model_instance):
    return {
        c.key: getattr(model_instance, c.key)
        for c in inspect(model_instance).mapper.column_attrs
    }


class CourseGroup(MappedAsDataclass, db.Model, unsafe_hash=True):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    link: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    picture_url: Mapped[str] = mapped_column(String, nullable=False)

    def get_courses(self) -> Sequence[Course]:
        return Course.get_by_course_group(self)

    @staticmethod
    def get_all() -> Sequence[CourseGroup]:
        return db.session.scalars(select(CourseGroup)).all()

    @staticmethod
    def get_all_with_courses():
        course_groups = db.session.scalars(select(CourseGroup)).all()
        courses = db.session.scalars(select(Course)).all()

        course_groups_dict = {
            course_group.id: {**to_dict(course_group), "course_list": []}
            for course_group in course_groups
        }

        for course in courses:
            course_groups_dict[course.course_group_id]["course_list"].append(
                to_dict(course)
            )

        return list(course_groups_dict.values())

    @staticmethod
    def get_by_name(name: str) -> CourseGroup | None:
        return db.session.scalar(select(CourseGroup).where(CourseGroup.name == name))

    @staticmethod
    def get_by_id(id: int) -> CourseGroup | None:
        return db.session.scalar(select(CourseGroup).where(CourseGroup.id == int(id)))

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
        return db.session.scalar(select(CourseGroup).where(CourseGroup.link == link))

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
        return db.session.scalars(select(Course)).all()

    @staticmethod
    def get_by_id(id: int) -> Course | None:
        return db.session.scalar(select(Course).where(Course.id == int(id)))

    @staticmethod
    def delete_by_id(id: int) -> None:
        if course := Course.get_by_id(int(id)):
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
            select(Course).where(Course.course_group == course_group)
        ).all()


class Group(MappedAsDataclass, db.Model, unsafe_hash=True):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String, nullable=False, init=True)
    description: Mapped[str] = mapped_column(String, nullable=False, init=True)
    duration: Mapped[str] = mapped_column(String, nullable=False, init=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False, init=True)
    course_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey("course.id"), init=True, nullable=False
    )

    course: Mapped[Course] = relationship(Course, backref="groups", init=False)

    @staticmethod
    def get_all() -> Sequence[Group]:
        return db.session.scalars(select(Group)).all()

    @staticmethod
    def get_by_id(id: int) -> Group | None:
        return db.session.scalar(select(Group).where(Group.id == int(id)))

    @staticmethod
    def get_by_course_id(course_id: int) -> Sequence[Group]:
        return db.session.scalars(
            select(Group).where(Group.course_id == course_id)
        ).all()


class Timetable(MappedAsDataclass, db.Model, unsafe_hash=True):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    day: Mapped[str] = mapped_column(String, nullable=False, init=True)
    time: Mapped[str] = mapped_column(String, nullable=False, init=True)
    group_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey("group.id"), init=True, nullable=False
    )

    group: Mapped[Group] = relationship(Group, backref="timetable", init=False)

    @staticmethod
    def get_all() -> Sequence[Timetable]:
        return db.session.scalars(select(Timetable)).all()

    @staticmethod
    def get_by_id(id: int) -> Timetable | None:
        return db.session.scalar(select(Timetable).where(Timetable.id == int(id)))

    @staticmethod
    def get_by_group_id(group_id: int) -> Sequence[Timetable]:
        return db.session.scalars(
            select(Timetable).where(Timetable.group_id == group_id)
        ).all()

    @staticmethod
    def get_by_course_id(course_id):
        return db.session.scalars(
            select(Timetable, Group, Course)
            .join(Group, Timetable.group_id == Group.id)
            .join(Course, Group.course_id == Course.id)
            .where(Course.id == course_id)
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
        return db.session.scalars(select(Teacher).limit(max)).all()

    @staticmethod
    def get_by_id(id: int) -> Teacher | None:
        return db.session.scalar(select(Teacher).where(Teacher.id == int(id)))

    @staticmethod
    def delete_by_id(id: int) -> None:
        if teacher := Teacher.get_by_id(int(id)):
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
        return db.session.scalars(select(Staff).limit(max)).all()

    @staticmethod
    def get_by_id(id: int) -> Staff | None:
        return db.session.scalar(select(Staff).where(Staff.id == int(id)))

    @staticmethod
    def delete_by_id(id: int) -> None:
        if staff := Staff.get_by_id(int(id)):
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


class EventType(MappedAsDataclass, db.Model, unsafe_hash=True):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    color: Mapped[str] = mapped_column(String, nullable=False)

    events: Mapped[list[Event]] = relationship("Event", uselist=True, init=False, backref="event_type")

    @staticmethod
    def get_all() -> Sequence[EventType]:
        return db.session.scalars(select(EventType)).all()

    @staticmethod
    def get_by_name(name: str) -> EventType | None:
        event_type = db.session.scalar(select(EventType).where(EventType.name == name))
        return event_type

    @staticmethod
    def get_by_id(id: int) -> EventType | None:
        return db.session.scalar(select(EventType).where(EventType.id == int(id)))

    @staticmethod
    def delete_by_id(id: int) -> None:
        if event_type := EventType.get_by_id(int(id)):
            db.session.delete(event_type)
            db.session.commit()
        else:
            raise ValueError(f"Event type with id {id} does not exist")


class Event(MappedAsDataclass, db.Model, unsafe_hash=True):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    event_type_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("event_type.id"))

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
        return db.session.scalars(select(Event)).all()

    @staticmethod
    def get_all_with_types():
        return (
            db.session.scalars(select(EventType).options(joinedload(EventType.events)))
            .unique()
            .all()
        )

    @staticmethod
    def get_this_month() -> Sequence[Event]:
        return db.session.scalars(
            select(Event, EventType.color)
            .join(EventType, Event.event_type_id == EventType.id)
            .where(
                Event.date >= datetime.date.today().replace(day=1),
                Event.event_type_id == EventType.id,
            )
            .order_by(Event.date)
        ).all()

    @staticmethod
    def get_by_month(month: int, year: int):
        return db.session.execute(
            select(Event, EventType.color)
            .join(EventType, Event.event_type_id == EventType.id)
            .where(
                extract("month", Event.date) == month,
                extract("year", Event.date) == year,
                Event.event_type_id == EventType.id,
            )
        ).all()

    @staticmethod
    def get_by_date(date: datetime.date) -> Sequence[Event]:
        return db.session.scalars(select(Event).where(Event.date == date)).all()

    @staticmethod
    def get_by_date_range(start_date: datetime.date, end_date: datetime.date):
        return db.session.execute(
            select(Event, EventType.color)
            .join(EventType, Event.event_type_id == EventType.id)
            .where(
                Event.date.between(start_date, end_date),
                Event.event_type_id == EventType.id,
            )
        ).all()

    @staticmethod
    def get_by_id(id: int) -> Event | None:
        return db.session.scalar(select(Event).where(Event.id == int(id)))

    @staticmethod
    def delete_by_id(id: int) -> None:
        if event_ := Event.get_by_id(int(id)):
            db.session.delete(event_)
            db.session.commit()
        else:
            raise ValueError(f"Event with id {id} does not exist")


class Feedback(MappedAsDataclass, db.Model, unsafe_hash=True):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    created_at: Mapped[datetime.date] = mapped_column(Date, nullable=False, init=False)
    name: Mapped[str] = mapped_column(String, nullable=False, init=True)
    message: Mapped[str] = mapped_column(String, nullable=False, init=True)
    email: Mapped[str] = mapped_column(String, nullable=True, init=False)
    number: Mapped[str] = mapped_column(String, nullable=True, init=False)
    picture_url: Mapped[str] = mapped_column(String, nullable=True, init=False)
    course: Mapped[str] = mapped_column(String, nullable=True, init=False)
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, init=False
    )

    @staticmethod
    def get_all() -> Sequence[Feedback]:
        return db.session.scalars(select(Feedback)).all()

    @staticmethod
    def get_all_verified() -> Sequence[Feedback]:
        return db.session.scalars(select(Feedback).where(Feedback.is_verified)).all()

    @staticmethod
    def get_by_id(id: int) -> Feedback | None:
        return db.session.scalar(select(Feedback).where(Feedback.id == int(id)))

    @staticmethod
    def delete_by_id(id: int) -> None:
        if feedback := Feedback.get_by_id(int(id)):
            db.session.delete(feedback)
            db.session.commit()


class Toefl(MappedAsDataclass, db.Model, unsafe_hash=True):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    test_taker_id: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    reading: Mapped[int] = mapped_column(Integer, nullable=True)
    listening: Mapped[int] = mapped_column(Integer, nullable=True)
    speaking: Mapped[int] = mapped_column(Integer, nullable=True)
    writing: Mapped[int] = mapped_column(Integer, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    @property
    def total(self) -> int:
        return self.reading + self.listening + self.speaking + self.writing

    @property
    def auca_total(self) -> int:
        return self.reading + self.listening + self.writing

    @staticmethod
    def get_all() -> Sequence[Toefl]:
        return db.session.scalars(select(Toefl)).all()

    @staticmethod
    def get_by_id(id: int) -> Toefl | None:
        return db.session.scalar(select(Toefl).where(Toefl.id == int(id)))

    @staticmethod
    def get_all_by_date(date: datetime.date) -> Sequence[Toefl]:
        return db.session.scalars(
            select(Toefl)
            .where(Toefl.date == date)
            .order_by(Toefl.is_published, Toefl.test_taker_id)
        ).all()

    @staticmethod
    def get_latest_results() -> Sequence[Toefl] | None:
        return db.session.scalars(
            select(Toefl)
            .where(Toefl.date == select(db.func.max(Toefl.date)).scalar_subquery())
            .order_by(Toefl.is_published, Toefl.test_taker_id)
        ).all()

    @staticmethod
    def get_pagination_dates(
        date: datetime.date,
    ):
        next_date = db.session.scalar(
            select(Toefl.date).where(Toefl.date > date).order_by(Toefl.date).limit(1)
        )
        previous_date = db.session.scalar(
            select(Toefl.date)
            .where(Toefl.date < date)
            .order_by(Toefl.date.desc())
            .limit(1)
        )
        return previous_date, next_date

    @staticmethod
    def delete_by_id(id: int) -> None:
        if toefl := Toefl.get_by_id(int(id)):
            db.session.delete(toefl)
            db.session.commit()

    @staticmethod
    def delete_by_date(date: datetime.date) -> None:
        toefls = Toefl.get_all_by_date(date)
        for toefl in toefls:
            db.session.delete(toefl)
        db.session.commit()


class ToeflRegistration(MappedAsDataclass, db.Model, unsafe_hash=True):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    handled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    @staticmethod
    def get_all() -> Sequence[ToeflRegistration]:
        return db.session.scalars(select(ToeflRegistration)).all()

    @staticmethod
    def get_all_unhandled() -> Sequence[ToeflRegistration]:
        return db.session.scalars(
            select(ToeflRegistration).where(ToeflRegistration.handled.is_(False))  # noqa
        ).all()

    @staticmethod
    def get_by_id(id: int) -> ToeflRegistration | None:
        return db.session.scalar(
            select(ToeflRegistration).where(ToeflRegistration.id == int(id))
        )

    @staticmethod
    def get_all_by_date(date: datetime.date) -> Sequence[ToeflRegistration]:
        return db.session.scalars(
            select(ToeflRegistration).where(
                func.date(ToeflRegistration.created_at) == date
            )
        ).all()

    @staticmethod
    def get_pagination(page: int, per_page: int = 5) -> Pagination:
        query = (
            select(ToeflRegistration)
            .where(ToeflRegistration.handled.is_(True))
            .order_by(ToeflRegistration.created_at.desc())
        )
        pagination = db.paginate(select=query, page=page, per_page=per_page)
        return pagination


class Registration(MappedAsDataclass, db.Model, unsafe_hash=True):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    handled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    @staticmethod
    def get_all() -> Sequence[Registration]:
        return db.session.scalars(select(Registration)).all()

    @staticmethod
    def get_all_unhandled() -> Sequence[Registration]:
        return db.session.scalars(
            select(Registration).where(Registration.handled.is_(False))  # noqa
        ).all()

    @staticmethod
    def get_by_id(id: int) -> Registration | None:
        return db.session.scalar(select(Registration).where(Registration.id == int(id)))

    @staticmethod
    def get_all_by_date(date: datetime.date) -> Sequence[Registration]:
        return db.session.scalars(
            select(Registration).where(func.date(Registration.created_at) == date)
        ).all()

    @staticmethod
    def get_pagination(page: int, per_page: int = 5) -> Pagination:
        query = (
            select(Registration)
            .where(Registration.handled.is_(True))
            .order_by(Registration.created_at.desc())
        )
        pagination = db.paginate(select=query, page=page, per_page=per_page)
        return pagination
