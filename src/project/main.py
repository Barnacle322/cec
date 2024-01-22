import calendar
import datetime

from flask import Blueprint, jsonify, render_template, request

from .extenstions import login_manager
from .models import Course, CourseGroup, Event, Staff, Teacher, User

main = Blueprint("main", __name__)


def generate_month_matrix(month: int, year: int) -> dict:
    month_data = {"month": month, "year": year, "matrix": []}
    month_calendar = calendar.monthcalendar(year, month)
    for week in month_calendar:
        week_matrix = []
        for day in week:
            if day == 0:
                week_matrix.append({"day": "", "events": []})
            else:
                date = datetime.date(year, month, day)
                event_colors = list(
                    {event.event_type.color for event in Event.get_by_date(date)}
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
    course_groups = CourseGroup.get_all()
    return render_template(
        "index.html",
        courses=course_groups,
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
    for event in events:
        events_serialized.append(
            {
                "name": event.name,
                "description": event.description,
                "event_color": event.event_type.color,
                "date": str(event.date),
                "date_string": event.date_string,
            }
        )
    return jsonify(events_serialized)
