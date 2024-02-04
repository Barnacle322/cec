import csv
import datetime
import os

from flask import Blueprint, redirect, render_template, request, url_for
from xlsx2csv import Xlsx2csv

from .extenstions import db
from .models import CourseGroup, EventType, Feedback, Staff, Teacher, Toefl
from .utils.decor import admin_required
from .utils.status_enum import Status, StatusType
from .views.course import (
    AddCourseGroupView,
    AddCourseView,
    DeleteCourseGroupView,
    DeleteCourseView,
    EditCourseGroupView,
    EditCourseView,
)
from .views.event import (
    AddEventTypeView,
    AddEventView,
    DeleteEventTypeView,
    DeleteEventView,
    EditEventTypeView,
    EditEventView,
)
from .views.people import (
    AddStaffView,
    AddTeacherView,
    DeleteStaffView,
    DeleteTeacherView,
    EditStaffView,
    EditTeacherView,
)

admin = Blueprint("admin", __name__)


@admin.route("/")
@admin_required
def index():
    return render_template("admin/index.html")


@admin.route("/courses")
@admin_required
def courses():
    course_dict = {}
    course_groups = CourseGroup.get_all()
    for course_group in course_groups:
        courses = course_group.get_courses()
        course_dict[course_group] = courses

    return render_template("admin/course/courses.html", course_dict=course_dict)


@admin.route("/course/<course_name>")
@admin_required
def course(course_name):
    return render_template("admin/course/course.html", course_name=course_name)


@admin.route("/events")
@admin_required
def events():
    event_dict = {}
    event_types = EventType.get_all()
    for event_type in event_types:
        event_types = event_type.get_events()
        event_dict[event_type] = event_types

    return render_template("admin/events.html", event_dict=event_dict)


@admin.route("/people")
@admin_required
def people():
    teachers = Teacher.get_all()
    staff = Staff.get_all()
    return render_template("admin/people/people.html", teachers=teachers, staff=staff)


@admin.route("/toefl")
@admin_required
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
        "admin/toefl.html", pagination=pagination, results=results, date=date
    )


@admin.route("/toefl/add", methods=["GET", "POST"])
def toefl_add():
    if request.method == "POST":
        file = request.files.get("file")
        date_str = request.form.get("date")
        if not date_str or not file:
            status = Status(
                StatusType.ERROR,
                "Пожалуйста, укажите дату и загрузите файл с результатами TOEFL.",
            ).get_status()
            return redirect(url_for("admin.toefl", _external=False, **status))

        date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

        if file.filename.split(".")[-1] in ["xlsx", "xls"]:  # type: ignore
            file.save("./src/project/static/toefl/toefl.xlsx")
            Xlsx2csv(
                "./src/project/static/toefl/toefl.xlsx", outputencoding="utf-8"
            ).convert("./src/project/static/toefl/toefl.csv")
            os.remove("./src/project/static/toefl/toefl.xlsx")

            with open(
                "./src/project/static/toefl/toefl.csv", newline="", encoding="utf-8"
            ) as f:
                reader = csv.reader(f, dialect="excel")

                header = [x.upper() for x in next(reader)]
                if header != [
                    "ID",
                    "READING",
                    "WRITING",
                    "SPEAKING",
                    "LISTENING",
                ]:
                    status = Status(
                        StatusType.ERROR,
                        "Неверный формат файла. Первая строка должна содержать заголовки столбцов: ID, READING, WRITING, LISTENING, SPEAKING.",
                    ).get_status()
                    return redirect(url_for("admin.toefl", _external=False, **status))
                toefl_results = []
                print("before delete")
                Toefl.delete_by_date(date)
                for line in reader:
                    toefl_results.append(
                        Toefl(
                            test_taker_id=line[0],
                            reading=int(line[1]),
                            writing=int(line[2]),
                            speaking=int(line[3]),
                            listening=int(line[4]),
                            date=date,
                        )
                    )
                db.session.add_all(toefl_results)
                db.session.commit()

                status = Status(
                    StatusType.SUCCESS, "Результаты TOEFL успешно добавлены."
                ).get_status()
                return redirect(url_for("admin.toefl", _external=False, **status))
        else:
            status = Status(
                StatusType.ERROR,
                "Неверный формат файла. Пожалуйста, загрузите файл в формате .xlsx или .xls",
            ).get_status()
            return redirect(url_for("admin.toefl", _external=False, **status))

    return render_template("admin/toefl/add_toefl.html")


@admin.get("/toefl/check/<date>")
@admin_required
def toefl_check(date):
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    results = Toefl.get_all_by_date(date)

    return "1" if results else "0"


@admin.get("/feedback")
@admin_required
def feedback():
    feedbacks = Feedback.get_all()
    return render_template("admin/feedback.html", feedbacks=feedbacks)


admin.add_url_rule(
    "/teacher/delete/<int:teacher_id>",
    view_func=DeleteTeacherView.as_view("delete_teacher"),
)
admin.add_url_rule("/teacher/add", view_func=AddTeacherView.as_view("add_teacher"))
admin.add_url_rule(
    "/teacher/edit/<int:teacher_id>", view_func=EditTeacherView.as_view("edit_teacher")
)

admin.add_url_rule("/staff/add", view_func=AddStaffView.as_view("add_staff"))
admin.add_url_rule(
    "/staff/edit/<int:staff_id>", view_func=EditStaffView.as_view("edit_staff")
)
admin.add_url_rule(
    "/staff/delete/<int:staff_id>", view_func=DeleteStaffView.as_view("delete_staff")
)


admin.add_url_rule(
    "/course_group/add", view_func=AddCourseGroupView.as_view("add_course_group")
)
admin.add_url_rule(
    "/course_group/edit/<int:course_group_id>",
    view_func=EditCourseGroupView.as_view("edit_course_group"),
)
admin.add_url_rule(
    "/course_group/delete/<int:course_group_id>",
    view_func=DeleteCourseGroupView.as_view("delete_course_group"),
)

admin.add_url_rule(
    "/course/add",
    view_func=AddCourseView.as_view("add_course"),
)
admin.add_url_rule(
    "/course/edit/<int:course_id>",
    view_func=EditCourseView.as_view("edit_course"),
)
admin.add_url_rule(
    "/course/delete/<int:course_id>",
    view_func=DeleteCourseView.as_view("delete_course"),
)


admin.add_url_rule(
    "/event_type/add", view_func=AddEventTypeView.as_view("add_event_type")
)
admin.add_url_rule(
    "/event_type/edit/<int:event_type_id>",
    view_func=EditEventTypeView.as_view("edit_event_type"),
)
admin.add_url_rule(
    "/event_type/delete/<int:event_type_id>",
    view_func=DeleteEventTypeView.as_view("delete_event_type"),
)

admin.add_url_rule("/event/add", view_func=AddEventView.as_view("add_event"))
admin.add_url_rule(
    "/event/edit/<int:event_id>", view_func=EditEventView.as_view("edit_event")
)
admin.add_url_rule(
    "/event/delete/<int:event_id>",
    view_func=DeleteEventView.as_view("delete_event"),
)
