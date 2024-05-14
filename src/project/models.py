from __future__ import annotations

import datetime
from collections.abc import Sequence
from sqlite3 import Connection as SQLite3Connection

from flask import current_app, session
from flask_login import UserMixin
from flask_sqlalchemy.pagination import Pagination
from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Integer,
    String,
    event,
    extract,
    func,
    select,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    Mapped,
    MappedAsDataclass,
    joinedload,
    mapped_column,
    relationship,
)

from .extenstions import db
from .utils.storage import delete_blob_from_url


class User(UserMixin, MappedAsDataclass, db.Model, unsafe_hash=True):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    @staticmethod
    def delete_by_id(id: int) -> None:
        if user := User.get_by_id(int(id)):
            db.session.delete(user)
            db.session.commit()

    @staticmethod
    def get_by_id(id: int) -> User | None:
        return db.session.scalar(select(User).where(User.id == int(id)))

    @staticmethod
    def get_by_username(username: str) -> User | None:
        return db.session.scalar(select(User).where(User.username == username))

    @staticmethod
    def get_all() -> Sequence[User]:
        return db.session.scalars(select(User)).all()


class CourseGroup(MappedAsDataclass, db.Model, unsafe_hash=True):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    _name: Mapped[dict] = mapped_column(JSON, nullable=True)
    _description: Mapped[dict] = mapped_column(JSON, nullable=True)
    slug: Mapped[str] = mapped_column(
        String,
        nullable=False,
        unique=True,
    )
    picture_url: Mapped[str] = mapped_column(String, nullable=False)

    courses: Mapped[list[Course]] = relationship(
        "Course", uselist=True, init=False, backref="course_group"
    )

    @property
    def name(self):
        lang = session.get("lang", "ru")
        return self._name.get(lang, self._name.get("ru"))

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def description(self):
        lang = session.get("lang", "ru")
        return self._description.get(lang, self._description.get("ru"))

    @description.setter
    def description(self, value):
        self._description = value

    @staticmethod
    def get_all() -> Sequence[CourseGroup]:
        return db.session.scalars(select(CourseGroup)).all()

    @staticmethod
    def get_all_with_courses():
        return (
            db.session.scalars(
                select(CourseGroup).options(joinedload(CourseGroup.courses))
            )
            .unique()
            .all()
        )

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
    def get_by_slug(slug: str) -> CourseGroup | None:
        return db.session.scalar(select(CourseGroup).where(CourseGroup.slug == slug))


class Course(MappedAsDataclass, db.Model, unsafe_hash=True):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    _name: Mapped[dict] = mapped_column(JSON, nullable=False)
    _description: Mapped[dict] = mapped_column(JSON, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    picture_url: Mapped[str] = mapped_column(String, nullable=False)
    course_group_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey("course_group.id")
    )

    @property
    def name(self):
        lang = session.get("lang", "ru")
        return self._name.get(lang, self._name.get("ru"))

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def description(self):
        lang = session.get("lang", "ru")
        return self._description.get(lang, self._description.get("ru"))

    @description.setter
    def description(self, value):
        self._description = value

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
    def get_by_course_group_id(course_group_id: int | None) -> Sequence[Course]:
        if not course_group_id:
            return Course.get_all()
        return db.session.scalars(
            select(Course).where(Course.course_group_id == course_group_id)
        ).all()

    @staticmethod
    def get_by_slug(slug: str) -> Course | None:
        return db.session.scalar(select(Course).where(Course.slug == slug))


class Timetable(MappedAsDataclass, db.Model, unsafe_hash=True):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    _name: Mapped[dict] = mapped_column(JSON, nullable=False, init=True)
    _description: Mapped[dict] = mapped_column(JSON, nullable=False, init=True)
    _duration: Mapped[dict] = mapped_column(JSON, nullable=False, init=True)
    _price: Mapped[dict] = mapped_column(JSON, nullable=False, init=True)
    json_data: Mapped[dict] = mapped_column(JSON, nullable=False, init=True)
    course_position: Mapped[int] = mapped_column(
        Integer, nullable=False, init=True, autoincrement=True
    )
    course_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey("course.id"), init=True, nullable=False
    )

    course: Mapped[Course] = relationship(Course, backref="timetables", init=False)

    @property
    def name(self):
        lang = session.get("lang", "ru")
        return self._name.get(lang, self._name.get("ru"))

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def description(self):
        lang = session.get("lang", "ru")
        return self._description.get(lang, self._description.get("ru"))

    @description.setter
    def description(self, value):
        self._description = value

    @property
    def duration(self):
        lang = session.get("lang", "ru")
        return self._duration.get(lang, self._duration.get("ru"))

    @duration.setter
    def duration(self, value):
        self._duration = value

    @property
    def price(self):
        lang = session.get("lang", "ru")
        return self._price.get(lang, self._price.get("ru"))

    @price.setter
    def price(self, value):
        self._price = value

    @staticmethod
    def get_all() -> Sequence[Timetable]:
        return db.session.scalars(
            select(Timetable).order_by(Timetable.course_position)
        ).all()

    @staticmethod
    def get_by_id(id: int) -> Timetable | None:
        return db.session.scalar(select(Timetable).where(Timetable.id == int(id)))

    @staticmethod
    def get_by_course_id(course_id: int):
        return db.session.scalars(
            select(Timetable)
            .where(Timetable.course_id == course_id)
            .order_by(Timetable.course_position)
        ).all()

    @staticmethod
    def delete_by_id(id: int) -> None:
        if timetable := Timetable.get_by_id(int(id)):
            db.session.delete(timetable)
            db.session.commit()
        else:
            raise ValueError(f"Timetable with id {id} does not exist")


class Teacher(MappedAsDataclass, db.Model, unsafe_hash=True):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    _name: Mapped[dict] = mapped_column(JSON, nullable=False)
    _description: Mapped[dict] = mapped_column(JSON, nullable=True)
    _bio: Mapped[dict] = mapped_column(JSON, nullable=True)
    picture_url: Mapped[str] = mapped_column(String, nullable=True)

    @property
    def name(self):
        lang = session.get("lang", "ru")
        return self._name.get(lang, self._name.get("ru"))

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def description(self):
        lang = session.get("lang", "ru")
        return self._description.get(lang, self._description.get("ru"))

    @description.setter
    def description(self, value):
        self._description = value

    @property
    def bio(self):
        lang = session.get("lang", "ru")
        return self._bio.get(lang, self._bio.get("ru"))

    @bio.setter
    def bio(self, value):
        self._bio = value

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


class Staff(MappedAsDataclass, db.Model, unsafe_hash=True):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    _name: Mapped[dict] = mapped_column(JSON, nullable=False)
    _description: Mapped[dict] = mapped_column(JSON, nullable=True)
    picture_url: Mapped[str] = mapped_column(String, nullable=True)

    @property
    def name(self):
        lang = session.get("lang", "ru")
        return self._name.get(lang, self._name.get("ru"))

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def description(self):
        lang = session.get("lang", "ru")
        return self._description.get(lang, self._description.get("ru"))

    @description.setter
    def description(self, value):
        self._description = value

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
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    _name: Mapped[dict] = mapped_column(JSON, nullable=False)
    _description: Mapped[dict] = mapped_column(JSON, nullable=True)
    color: Mapped[str] = mapped_column(String, nullable=False)

    events: Mapped[list[Event]] = relationship(
        "Event", uselist=True, init=False, backref="event_type"
    )

    @property
    def name(self):
        lang = session.get("lang", "ru")
        return self._name.get(lang, self._name.get("ru"))

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def description(self):
        lang = session.get("lang", "ru")
        return self._description.get(lang, self._description.get("ru"))

    @description.setter
    def description(self, value):
        self._description = value

    @staticmethod
    def get_all() -> Sequence[EventType]:
        return db.session.scalars(select(EventType)).all()

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
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    _name: Mapped[dict] = mapped_column(JSON, nullable=False)
    _description: Mapped[dict] = mapped_column(JSON, nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    event_type_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("event_type.id"))

    @property
    def name(self):
        lang = session.get("lang", "ru")
        return self._name.get(lang, self._name.get("ru"))

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def description(self):
        lang = session.get("lang", "ru")
        return self._description.get(lang, self._description.get("ru"))

    @description.setter
    def description(self, value):
        self._description = value

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
            .order_by(Event.date)
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
    listening: Mapped[int] = mapped_column(Integer, nullable=True)
    grammar: Mapped[int] = mapped_column(Integer, nullable=True)
    reading: Mapped[int] = mapped_column(Integer, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def calculate_listening(self):
        lookup = {
            0: 200,
            1: 240,
            2: 250,
            3: 270,
            4: 280,
            5: 290,
            6: 300,
            7: 310,
            8: 320,
            9: 330,
            10: 340,
            11: 350,
            12: 360,
            13: 370,
            14: 390,
            15: 400,
            16: 400,
            17: 410,
            18: 420,
            19: 430,
            20: 430,
            21: 440,
            22: 440,
            23: 450,
            24: 460,
            25: 460,
            26: 470,
            27: 470,
            28: 480,
            29: 480,
            30: 490,
            31: 500,
            32: 500,
            33: 510,
            34: 520,
            35: 520,
            36: 530,
            37: 540,
            38: 550,
            39: 550,
            40: 560,
            41: 570,
            42: 580,
            43: 590,
            44: 600,
            45: 610,
            46: 610,
            47: 630,
            48: 640,
            49: 660,
            50: 680,
        }
        return lookup.get(self.listening, 0)

    def calculate_grammar(self):
        lookup = {
            0: 200,
            1: 210,
            2: 220,
            3: 240,
            4: 250,
            5: 260,
            6: 280,
            7: 290,
            8: 300,
            9: 320,
            10: 340,
            11: 340,
            12: 360,
            13: 370,
            14: 380,
            15: 390,
            16: 400,
            17: 410,
            18: 420,
            19: 430,
            20: 440,
            21: 450,
            22: 460,
            23: 470,
            24: 480,
            25: 490,
            26: 500,
            27: 510,
            28: 520,
            29: 540,
            30: 540,
            31: 550,
            32: 560,
            33: 580,
            34: 590,
            35: 600,
            36: 620,
            37: 640,
            38: 660,
            39: 670,
            40: 680,
            41: 680,
            42: 680,
            43: 680,
            44: 680,
            45: 680,
            46: 680,
            47: 680,
            48: 680,
            49: 680,
            50: 680,
        }
        return lookup.get(self.grammar, 0)

    def calculate_reading(self):
        lookup = {
            0: 210,
            1: 220,
            2: 230,
            3: 230,
            4: 240,
            5: 250,
            6: 260,
            7: 270,
            8: 280,
            9: 280,
            10: 290,
            11: 300,
            12: 310,
            13: 330,
            14: 340,
            15: 350,
            16: 360,
            17: 370,
            18: 380,
            19: 390,
            20: 400,
            21: 410,
            22: 420,
            23: 430,
            24: 430,
            25: 440,
            26: 450,
            27: 460,
            28: 460,
            29: 470,
            30: 480,
            31: 480,
            32: 490,
            33: 500,
            34: 510,
            35: 520,
            36: 520,
            37: 530,
            38: 540,
            39: 540,
            40: 550,
            41: 560,
            42: 570,
            43: 580,
            44: 590,
            45: 600,
            46: 610,
            47: 630,
            48: 650,
            49: 660,
            50: 670,
        }
        return lookup.get(self.reading, 0)

    @property
    def total(self) -> int:
        return round(
            (
                self.calculate_grammar()
                + self.calculate_listening()
                + self.calculate_reading()
            )
            / 3
        )

    @property
    def auca_total(self) -> int:
        return round((self.calculate_grammar() + self.calculate_reading()) / 2)

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
    handled_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime, nullable=True, init=False
    )
    handled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, init=False
    )

    @staticmethod
    def get_all() -> Sequence[ToeflRegistration]:
        return db.session.scalars(select(ToeflRegistration)).all()

    @staticmethod
    def get_all_unhandled() -> Sequence[ToeflRegistration]:
        return db.session.scalars(
            select(ToeflRegistration).where(ToeflRegistration.handled.is_(False))
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
            .order_by(ToeflRegistration.handled_at.desc())
        )
        pagination = db.paginate(select=query, page=page, per_page=per_page)
        return pagination


class Registration(MappedAsDataclass, db.Model, unsafe_hash=True):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    course_info: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    handled_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime, nullable=True, init=False
    )
    handled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, init=False
    )

    @staticmethod
    def get_all() -> Sequence[Registration]:
        return db.session.scalars(select(Registration)).all()

    @staticmethod
    def get_all_unhandled() -> Sequence[Registration]:
        return db.session.scalars(
            select(Registration)
            .where(Registration.handled.is_(False))
            .order_by(Registration.course_info)
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
            .order_by(Registration.handled_at.desc())
        )
        pagination = db.paginate(select=query, page=page, per_page=per_page)
        return pagination


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()
