from __future__ import annotations

import datetime
from collections.abc import Sequence
from enum import Enum

from flask_login import UserMixin
from sqlalchemy import Boolean, Date, DateTime, Integer, String, event, extract
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from .extenstions import db


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
    link: Mapped[str] = mapped_column(String, nullable=False)
    picture: Mapped[str] = mapped_column(String, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return super().__repr__()

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
    def get_by_link(link: str) -> CourseGroup | None:
        return db.session.scalar(db.select(CourseGroup).where(CourseGroup.link == link))

    @staticmethod
    def populate():
        programming = CourseGroup(
            name="Кодинг",
            description="Научитесь программировать на Python, Java, C++ и других языках программирования",
            link="coding",
            picture="http://127.0.0.1:5000/static/elements/coding.jpg",
        )
        dar = CourseGroup(
            name="Детская академия роста",
            description="Дайте ребенку возможность развиваться вместе с нами!",
            link="dar",
            picture="http://127.0.0.1:5000/static/elements/dar.jpg",
        )
        language = CourseGroup(
            name="Иностранные языки",
            description="Изучайте английский, немецкий, французский и другие языки",
            link="language",
            picture="http://127.0.0.1:5000/static/elements/languages.jpg",
        )
        business = CourseGroup(
            name="Бизнес",
            description="Научитесь создавать и развивать свой бизнес",
            link="business",
            picture="http://127.0.0.1:5000/static/elements/business.jpg",
        )
        preparation = CourseGroup(
            name="Подготовительные курсы",
            description="Мы поможем вам подготовиться к школе, ВУЗу или экзаменам",
            link="preparation",
            picture="http://127.0.0.1:5000/static/elements/preparation.jpg",
        )
        chess = CourseGroup(
            name="Шахматы",
            description="Изучайте шахматы с нами",
            link="chess",
            picture="http://127.0.0.1:5000/static/elements/chess.jpg",
        )
        db.session.add_all([programming, dar, language, business, preparation, chess])
        db.session.commit()


class Course(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    link: Mapped[str] = mapped_column(String, nullable=False)
    picture: Mapped[str] = mapped_column(String, nullable=False)
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
    def get_by_course_group(
        course_group: CourseGroup | None = None,
    ) -> Sequence[Course]:
        if not course_group:
            return Course.get_all()
        return db.session.scalars(
            db.select(Course).where(Course.course_group == course_group)
        ).all()

    @staticmethod
    def populate():
        programming = Course(
            name="Python",
            description="На этом курсе вы научитесь программировать на Python",
            link="python",
            picture="http://127.0.0.1:5000/static/elements/coding.jpg",
            course_group=CourseGroup.get_by_id(1),
        )
        dar = Course(
            name="C++",
            description="На этом курсе вы научитесь программировать на C++",
            link="cplusplus",
            picture="http://127.0.0.1:5000/static/elements/coding.jpg",
            course_group=CourseGroup.get_by_id(1),
        )
        language = Course(
            name="Cisco",
            description="На этом курсе вы узнаете про Cisco",
            link="cisco",
            picture="http://127.0.0.1:5000/static/elements/coding.jpg",
            course_group=CourseGroup.get_by_id(1),
        )
        business = Course(
            name="Data Science",
            description="На этом курсе вы узнаете про Data Science",
            link="datascience",
            picture="http://127.0.0.1:5000/static/elements/coding.jpg",
            course_group=CourseGroup.get_by_id(1),
        )
        preparation = Course(
            name="Курсы английского языка",
            description="На этом курсе вы узнаете про английский язык",
            link="english",
            picture="http://127.0.0.1:5000/static/elements/coding.jpg",
            course_group=CourseGroup.get_by_id(3),
        )
        chess = Course(
            name="Создай свою компьютерную игру",
            description="На этом курсе вы узнаете про создание компьютерных игр",
            link="computergame",
            picture="http://127.0.0.1:5000/static/elements/coding.jpg",
            course_group=CourseGroup.get_by_id(2),
        )
        db.session.add_all([programming, dar, language, business, preparation, chess])
        db.session.commit()


class Teacher(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    bio: Mapped[str] = mapped_column(String, nullable=False)
    picture: Mapped[str] = mapped_column(String, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return super().__repr__()

    @staticmethod
    def get_all(max: int = 9999) -> Sequence[Teacher]:
        return db.session.scalars(db.select(Teacher).limit(max)).all()

    @staticmethod
    def populate():
        alisa = Teacher(
            name="Алыбаева Алиса",
            description="Алыбаева Алиса - преподаватель по математике",
            bio="Алыбаева Алиса - преподаватель по математике.",
            picture="/static/elements/teachers/Алыбаева Алиса.jpg",
        )
        mira = Teacher(
            name="Алыбаева Мира",
            description="Алыбаева Мира - преподаватель по физике",
            bio="Алыбаева Мира - преподаватель по физике.",
            picture="/static/elements/teachers/Алыбаева Мира.jpg",
        )
        mariya = Teacher(
            name="ДеКастл Мария",
            description="ДеКастл Мария - преподаватель по химии",
            bio="ДеКастл Мария - преподаватель по химии.",
            picture="/static/elements/teachers/ДеКастл Мария.jpg",
        )
        asem = Teacher(
            name="Жунусова Асем",
            description="Жунусова Асем - преподаватель по биологии",
            bio="Жунусова Асем - преподаватель по биологии.",
            picture="/static/elements/teachers/Жунусова Асем.jpg",
        )
        aigul = Teacher(
            name="Каримова Айгуль",
            description="Каримова Айгуль - преподаватель по математике",
            bio="Каримова Айгуль - преподаватель по математике.",
            picture="/static/elements/teachers/Каримова Айгуль.jpg",
        )
        gulmira = Teacher(
            name="Молдомусаева Гульмира",
            description="Молдомусаева Гульмира - преподаватель по математике",
            bio="Молдомусаева Гульмира - преподаватель по математике.",
            picture="/static/elements/teachers/Молдомусаева Гульмира.jpg",
        )
        angela = Teacher(
            name="Пак Анжела",
            description="Пак Анжела - преподаватель по математике",
            bio="Пак Анжела - преподаватель по математике.",
            picture="/static/elements/teachers/Пак Анжела.jpg",
        )
        valentina = Teacher(
            name="Рындина Валентина",
            description="Рындина Валентина - преподаватель по математике",
            bio="Рындина Валентина - преподаватель по математике.",
            picture="/static/elements/teachers/Рындина Валентина.jpg",
        )
        liana = Teacher(
            name="Семенова Лиана",
            description="Семенова Лиана - преподаватель по математике",
            bio="Семенова Лиана - преподаватель по математике.",
            picture="/static/elements/teachers/Семенова Лиана.jpg",
        )
        leyla = Teacher(
            name="Серикова Лейла",
            description="Серикова Лейла - преподаватель по математике",
            bio="Серикова Лейла - преподаватель по математике.",
            picture="/static/elements/teachers/Серикова Лейла.jpg",
        )
        olga = Teacher(
            name="Скрипник Ольга",
            description="Скрипник Ольга - преподаватель по математике",
            bio="Скрипник Ольга - преподаватель по математике.",
            picture="/static/elements/teachers/Скрипник Ольга.jpg",
        )
        narisa = Teacher(
            name="Турдиева Нариса",
            description="Турдиева Нариса - преподаватель по математике",
            bio="Турдиева Нариса - преподаватель по математике.",
            picture="/static/elements/teachers/Турдиева Нариса.jpg",
        )
        anna = Teacher(
            name="Шевцова Анна",
            description="Шевцова Анна - преподаватель по математике",
            bio="Шевцова Анна - преподаватель по математике.",
            picture="/static/elements/teachers/Шевцова Анна.jpg",
        )
        gulkaiyr = Teacher(
            name="Эмилбекова Гулкайыр",
            description="Эмилбекова Гулкайыр - преподаватель по математике",
            bio="Эмилбекова Гулкайыр - преподаватель по математике.",
            picture="/static/elements/teachers/Эмилбекова Гулкайыр.jpg",
        )

        db.session.add_all(
            [
                alisa,
                mira,
                mariya,
                asem,
                aigul,
                gulmira,
                angela,
                valentina,
                liana,
                leyla,
                olga,
                narisa,
                anna,
                gulkaiyr,
            ]
        )
        db.session.commit()


class Staff(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    picture: Mapped[str] = mapped_column(String, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return super().__repr__()

    @staticmethod
    def get_all(max: int = 9999) -> Sequence[Staff]:
        return db.session.scalars(db.select(Staff).limit(max)).all()

    @staticmethod
    def populate():
        staff1 = Staff(
            name="Турдиева Нариса",
            description="Позиция",
            picture="/static/elements/teachers/Турдиева Нариса.jpg",
        )
        staff2 = Staff(
            name="Турдиева Нариса",
            description="Позиция",
            picture="/static/elements/teachers/Турдиева Нариса.jpg",
        )
        staff3 = Staff(
            name="Турдиева Нариса",
            description="Позиция",
            picture="/static/elements/teachers/Турдиева Нариса.jpg",
        )
        staff4 = Staff(
            name="Турдиева Нариса",
            description="Позиция",
            picture="/static/elements/teachers/Турдиева Нариса.jpg",
        )
        staff5 = Staff(
            name="Турдиева Нариса",
            description="Позиция",
            picture="/static/elements/teachers/Турдиева Нариса.jpg",
        )

        db.session.add_all([staff1, staff2, staff3, staff4, staff5])
        db.session.commit()


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


@event.listens_for(CourseGroup.__table__, "after_create")  # type: ignore
def populate_courselink(*args, **kwargs):
    CourseGroup.populate()


@event.listens_for(Course.__table__, "after_create")  # type: ignore
def populate_course(*args, **kwargs):
    Course.populate()


@event.listens_for(EventType.__table__, "after_create")  # type: ignore
def populate_event_type(*args, **kwargs):
    EventType.populate()


@event.listens_for(Event.__table__, "after_create")  # type: ignore
def populate_event(*args, **kwargs):
    Event.populate()


@event.listens_for(Teacher.__table__, "after_create")  # type: ignore
def populate_teacher(*args, **kwargs):
    Teacher.populate()
