import calendar
import datetime
import random

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from .extenstions import db, login_manager
from .models import (
    Course,
    CourseGroup,
    Event,
    Feedback,
    Registration,
    Staff,
    Teacher,
    Toefl,
    ToeflRegistration,
    User,
)

main = Blueprint("main", __name__)


def generate_month_matrix(month: int, year: int) -> dict:
    month_data = {"month": month, "year": year, "matrix": []}
    month_calendar = calendar.monthcalendar(year, month)

    start_date = datetime.date(year, month, 1)
    end_date = datetime.date(year, month, calendar.monthrange(year, month)[1])
    all_events = Event.get_by_date_range(start_date, end_date)

    for week in month_calendar:
        week_matrix = []
        for day in week:
            if day == 0:
                week_matrix.append({"day": "", "events": []})
            else:
                date = datetime.date(year, month, day)
                event_colors = list(
                    {
                        event_color
                        for event, event_color in all_events
                        if event.date == date
                    }
                )[0:3]
                week_matrix.append({"day": day, "events": event_colors})
        month_data["matrix"].append(week_matrix)
    return month_data


@login_manager.user_loader
def load_user(user_id: int) -> User | None:
    user = User.get_by_id(id=int(user_id))
    if user:
        return user
    return None


@main.route("/")
def index():
    success = None
    if args := request.args:
        success = True if args.get("success") == "true" else False

    course_groups = CourseGroup.get_all()
    feedbacks = Feedback.get_all_verified()
    hero_list = ["hero-1.jpg", "hero-2.jpg", "hero-3.jpg"]
    random_hero = random.choice(hero_list)
    return render_template(
        "index.html",
        course_groups=course_groups,
        feedbacks=feedbacks,
        random_hero=random_hero,
        success=success,
    )


@main.route("/courses")
def courses():
    course_groups = CourseGroup.get_all()
    query = request.args.get("course_group")
    course_group = CourseGroup.get_by_link(query) if query else None
    courses = Course.get_by_course_group(course_group)

    return render_template("courses.html", courses=courses, course_groups=course_groups)


@main.route("/course/<course_name>")
def course(course_name):
    return render_template("course.html", course_name=course_name)


@main.route("/calendar/<int:month>/<int:year>")
def send_calendar(month, year):
    return jsonify(generate_month_matrix(month, year))


@main.route("/about")
def about():
    staff = Staff.get_all()
    return render_template("about.html", staff=staff)


@main.route("/teachers")
def teachers():
    teachers = Teacher.get_all()
    return render_template("teachers.html", teachers=teachers)


@main.route("/events/<int:month>/<int:year>")
def send_events(month, year):
    events = Event.get_by_month(month, year)
    events_serialized = []
    for event, event_color in events:
        events_serialized.append(
            {
                "name": event.name,
                "description": event.description,
                "event_color": event_color,
                "date": str(event.date),
                "date_string": event.date_string,
            }
        )
    return jsonify(events_serialized)


@main.route("/toefl")
def toefl():
    if (date_str := request.args.get("date", type=str)) != "None" and date_str != None:
        try:
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            results = Toefl.get_all_by_date(date)
        except ValueError:
            date = datetime.date.today()
            results = Toefl.get_latest_results()
    else:
        results = Toefl.get_latest_results()
        date = results[0].date if results else datetime.date.today()

    pagination = Toefl.get_pagination_dates(date)
    return render_template(
        "toefl.html", date=date, results=results, pagination=pagination
    )


@main.get("/toefl/register")
def toefl_register():
    success = None
    if args := request.args:
        success = True if args.get("success") == "true" else False

    # Get today's date
    today = datetime.date.today()

    # Calculate the number of days until the next Monday (0) and Thursday (3)
    days_until_monday = (0 - today.weekday() + 7) % 7
    days_until_thursday = (3 - today.weekday() + 7) % 7

    # Get the next two Mondays
    next_monday = today + datetime.timedelta(days=days_until_monday)
    next_next_monday = next_monday + datetime.timedelta(days=7)

    # Get the next two Thursdays
    next_thursday = today + datetime.timedelta(days=days_until_thursday)
    next_next_thursday = next_thursday + datetime.timedelta(days=7)

    months_ru = {
        1: "Январь",
        2: "Февраль",
        3: "Март",
        4: "Апрель",
        5: "Май",
        6: "Июнь",
        7: "Июль",
        8: "Август",
        9: "Сентябрь",
        10: "Октябрь",
        11: "Ноябрь",
        12: "Декабрь",
    }

    available_dates = [
        {
            "date": f"Понедельник, {months_ru[next_monday.month]} {next_monday.day}, {next_monday.year}",
            "value": next_monday,
        },
        {
            "date": f"Понедельник, {months_ru[next_next_monday.month]} {next_next_monday.day}, {next_next_monday.year}",
            "value": next_next_monday,
        },
        {
            "date": f"Четверг, {months_ru[next_thursday.month]} {next_thursday.day}, {next_thursday.year}",
            "value": next_thursday,
        },
        {
            "date": f"Четверг, {months_ru[next_next_thursday.month]} {next_next_thursday.day}, {next_next_thursday.year}",
            "value": next_next_thursday,
        },
    ]
    available_dates = sorted(available_dates, key=lambda x: x["value"])

    return render_template(
        "toefl_register.html", success=success, available_dates=available_dates
    )


@main.post("/toefl/register")
def toefl_register_post():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    day = request.form.get("day")

    if not first_name or not last_name or not email or not phone or not day:
        return render_template("toefl_register.html", success=False)

    day = datetime.datetime.strptime(day, "%Y-%m-%d").date()

    try:
        registration = ToeflRegistration(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            date=day,
            created_at=datetime.datetime.now(
                tz=datetime.timezone(datetime.timedelta(hours=6))
            ),
        )
        db.session.add(registration)
        db.session.commit()
    except Exception as e:
        print(e)
        return render_template("toefl_register.html", success=False)

    return render_template("toefl_register.html", success=True)


@main.post("/register")
def register():
    name = request.form.get("name")
    phone = request.form.get("phone")

    if not name or not phone:
        return redirect(
            url_for("main.index", _anchor="registration-form", success="false")
        )

    try:
        registration = Registration(
            name=name,
            phone=phone,
            created_at=datetime.datetime.now(
                tz=datetime.timezone(datetime.timedelta(hours=6))
            ),
        )
        db.session.add(registration)
        db.session.commit()
    except Exception as e:
        print(e)
        return redirect(
            url_for("main.index", _anchor="registration-form", success="false")
        )

    return redirect(url_for("main.index", _anchor="registration-form", success="true"))
