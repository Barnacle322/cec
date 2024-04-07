from __future__ import annotations

import datetime
from collections.abc import Sequence
from enum import Enum

from flask import current_app
from flask_login import UserMixin
from sqlalchemy import Boolean, Date, DateTime, Integer, String, extract, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, MappedAsDataclass, mapped_column, relationship
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
        return db.session.scalar(db.select(cls).where(cls.id == int(id)))

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
        return db.session.scalar(
            db.select(CourseGroup).where(CourseGroup.id == int(id))
        )

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
        return db.session.scalar(db.select(Course).where(Course.id == int(id)))

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
        return db.session.scalar(db.select(Teacher).where(Teacher.id == int(id)))

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
        return db.session.scalars(db.select(Staff).limit(max)).all()

    @staticmethod
    def get_by_id(id: int) -> Staff | None:
        return db.session.scalar(db.select(Staff).where(Staff.id == int(id)))

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


class EventType(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    color: Mapped[str] = mapped_column(String, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return super().__repr__()

    def get_events(self) -> Sequence[Event]:
        return Event.get_by_event_type(self)

    @staticmethod
    def get_all() -> Sequence[EventType]:
        return db.session.scalars(db.select(EventType)).all()

    @staticmethod
    def get_by_name(name: str) -> EventType | None:
        event_type = db.session.scalar(
            db.select(EventType).where(EventType.name == name)
        )
        return event_type

    @staticmethod
    def get_by_id(id: int) -> EventType | None:
        return db.session.scalar(db.select(EventType).where(EventType.id == int(id)))

    @staticmethod
    def delete_by_id(id: int) -> None:
        if event_type := EventType.get_by_id(int(id)):
            db.session.delete(event_type)
            db.session.commit()
        else:
            raise ValueError(f"Event type with id {id} does not exist")

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
    def get_by_date_range(
        start_date: datetime.date, end_date: datetime.date
    ) -> Sequence[Event]:
        return db.session.scalars(
            db.select(Event).where(Event.date.between(start_date, end_date))
        ).all()

    @staticmethod
    def get_by_id(id: int) -> Event | None:
        return db.session.scalar(db.select(Event).where(Event.id == int(id)))

    @staticmethod
    def delete_by_id(id: int) -> None:
        if event_ := Event.get_by_id(int(id)):
            db.session.delete(event_)
            db.session.commit()
        else:
            raise ValueError(f"Event with id {id} does not exist")

    @staticmethod
    def get_by_event_type(
        event_type: EventType | None = None,
    ) -> Sequence[Event]:
        if not event_type:
            return Event.get_all()
        return db.session.scalars(
            db.select(Event).where(Event.event_type == event_type).order_by(Event.date)
        ).all()

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
        return db.session.scalars(db.select(Feedback)).all()

    @staticmethod
    def get_by_id(id: int) -> Feedback | None:
        return db.session.scalar(db.select(Feedback).where(Feedback.id == int(id)))

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
        return db.session.scalars(db.select(Toefl)).all()

    @staticmethod
    def get_by_id(id: int) -> Toefl | None:
        return db.session.scalar(db.select(Toefl).where(Toefl.id == int(id)))

    @staticmethod
    def get_all_by_date(date: datetime.date) -> Sequence[Toefl]:
        return db.session.scalars(
            db.select(Toefl)
            .where(Toefl.date == date)
            .order_by(Toefl.is_published, Toefl.test_taker_id)
        ).all()

    @staticmethod
    def get_latest_results() -> Sequence[Toefl] | None:
        return db.session.scalars(
            db.select(Toefl)
            .where(Toefl.date == db.select(db.func.max(Toefl.date)).scalar_subquery())
            .order_by(Toefl.is_published, Toefl.test_taker_id)
        ).all()

    @staticmethod
    def get_pagination_dates(
        date: datetime.date,
    ) -> tuple[datetime.date, datetime.date]:
        next_date = db.session.scalar(
            db.select(Toefl.date).where(Toefl.date > date).order_by(Toefl.date).limit(1)
        )
        previous_date = db.session.scalar(
            db.select(Toefl.date)
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

    @staticmethod
    def populate():
        toefl_results = (
            Toefl(
                test_taker_id="123456",
                reading=30,
                writing=30,
                speaking=30,
                listening=30,
                date=datetime.date(2024, 1, 1),
            ),
            Toefl(
                test_taker_id="123457",
                reading=30,
                writing=30,
                speaking=30,
                listening=30,
                date=datetime.date(2024, 1, 1),
            ),
            Toefl(
                test_taker_id="123458",
                reading=30,
                writing=30,
                speaking=30,
                listening=30,
                date=datetime.date(2024, 1, 1),
            ),
            Toefl(
                test_taker_id="123459",
                reading=30,
                writing=30,
                speaking=30,
                listening=30,
                date=datetime.date(2024, 1, 1),
            ),
            Toefl(
                test_taker_id="123460",
                reading=30,
                writing=30,
                speaking=30,
                listening=30,
                date=datetime.date(2024, 1, 1),
            ),
            Toefl(
                test_taker_id="123461",
                reading=30,
                writing=30,
                speaking=30,
                listening=30,
                date=datetime.date(2024, 1, 1),
            ),
            Toefl(
                test_taker_id="123462",
                reading=30,
                writing=30,
                speaking=30,
                listening=30,
                date=datetime.date(2024, 1, 1),
            ),
            Toefl(
                test_taker_id="123463",
                reading=30,
                writing=30,
                speaking=30,
                listening=30,
                date=datetime.date(2024, 1, 1),
            ),
        )
        db.session.add_all(toefl_results)
        db.session.commit()


class ToeflRegistration(MappedAsDataclass, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)

    @staticmethod
    def get_all() -> Sequence[ToeflRegistration]:
        return db.session.scalars(db.select(ToeflRegistration)).all()

    @staticmethod
    def get_by_id(id: int) -> ToeflRegistration | None:
        return db.session.scalar(
            db.select(ToeflRegistration).where(ToeflRegistration.id == int(id))
        )

    @staticmethod
    def get_all_by_date(date: datetime.date) -> Sequence[ToeflRegistration]:
        return db.session.scalars(
            db.select(ToeflRegistration).where(
                func.date(ToeflRegistration.created_at) == date
            )
        ).all()
