import csv
import datetime
import os

from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from xlsx2csv import Xlsx2csv

from .extenstions import db
from .models import (
    CourseGroup,
    Event,
    Feedback,
    Registration,
    Staff,
    Teacher,
    Timetable,
    Toefl,
    ToeflRegistration,
)
from .utils.decor import admin_required
from .utils.status_enum import Status, StatusType
from .views.course import (
    AddCourseGroupView,
    AddCourseView,
    AddTimetable,
    DeleteCourseGroupView,
    DeleteCourseView,
    DeleteTimetable,
    EditCourseGroupView,
    EditCourseView,
    EditTimetable,
)
from .views.event import (
    AddEventTypeView,
    AddEventView,
    DeleteEventTypeView,
    DeleteEventView,
    EditEventTypeView,
    EditEventView,
)
from .views.feedback import AddFeedbackView, DeleteFeedbackView, EditFeedbackView
from .views.people import (
    AddStaffView,
    AddTeacherView,
    DeleteStaffView,
    DeleteTeacherView,
    EditStaffView,
    EditTeacherView,
)

admin = Blueprint("admin", __name__)


@admin.route("/courses")
@admin_required
def courses():
    course_groups = CourseGroup.get_all_with_courses()
    timetables = Timetable.get_all()
    timetable_dict = {}
    for timetable in timetables:
        if not timetable_dict.get(timetable.course_id):
            timetable_dict[timetable.course_id] = list()
            timetable_dict[timetable.course_id].append(timetable)
        else:
            timetable_dict[timetable.course_id].append(timetable)

    return render_template(
        "admin/course/courses.html",
        course_groups=course_groups,
        timetables=timetable_dict,
    )


@admin.route("/events")
@admin_required
def events():
    events = Event.get_all_with_types()
    return render_template("admin/events.html", event_dict=events)


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
                header = [x.strip() for x in header if x != ""]
                if header != [
                    "ID",
                    "READING",
                    "WRITING",
                    "SPEAKING",
                    "LISTENING",
                ]:
                    status = Status(
                        StatusType.ERROR,
                        "Неверный формат файла. Первая строка должна содержать заголовки столбцов: ID, READING, WRITING, SPEAKING, LISTENING",
                    ).get_status()
                    return redirect(url_for("admin.toefl", _external=False, **status))

                toefl_results = []
                Toefl.delete_by_date(date)
                for line in reader:
                    line = [x.strip() for x in line if x != ""]
                    if len(line) != 0:
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


@admin.post("/toefl/publish")
@admin_required
def toefl_publish():
    checkboxes = request.form.getlist("selected")
    if not checkboxes:
        status = Status(
            StatusType.ERROR, "Пожалуйста, выберите хотя бы один результат TOEFL."
        ).get_status()
        return redirect(url_for("admin.toefl", _external=False, **status))

    for checkbox in checkboxes:
        result = Toefl.get_by_id(int(checkbox))
        if not result:
            status = Status(
                StatusType.ERROR,
                f"Результат TOEFL с ID {checkbox} не найден. Возможно, он был удален.",
            ).get_status()
            return redirect(url_for("admin.toefl", _external=False, **status))
        result.is_published = True
        db.session.commit()

    return redirect(url_for("admin.toefl"))


@admin.post("/toefl/unpublish")
@admin_required
def toefl_unpublish():
    checkboxes = request.form.getlist("selected")
    if not checkboxes:
        status = Status(
            StatusType.ERROR, "Пожалуйста, выберите хотя бы один результат TOEFL."
        ).get_status()
        return redirect(url_for("admin.toefl", _external=False, **status))

    for checkbox in checkboxes:
        result = Toefl.get_by_id(int(checkbox))
        if not result:
            status = Status(
                StatusType.ERROR,
                f"Результат TOEFL с ID {checkbox} не найден. Возможно, он был удален.",
            ).get_status()
            return redirect(url_for("admin.toefl", _external=False, **status))
        result.is_published = False
        db.session.commit()

    return redirect(url_for("admin.toefl"))


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


@admin.get("/")
@admin.get("/applications")
@admin_required
def applications():
    toefl_applications = ToeflRegistration.get_all_unhandled()
    applications = Registration.get_all_unhandled()
    return render_template(
        "admin/applications.html", toefl=toefl_applications, applications=applications
    )


@admin.post("/applications/toggle_handle/<type>/<int:id>")
@admin_required
def toggle_handle(type, id):
    if not type or not id:
        return jsonify({"error": "Invalid parameters", "handled": None})

    handled = None

    if type == "toefl":
        try:
            toefl = ToeflRegistration.get_by_id(id)
            if not toefl:
                raise AttributeError

            toefl.handled = not toefl.handled
            handled = toefl.handled
            db.session.commit()
        except AttributeError:
            return jsonify({"error": "TOEFL registration not found", "handled": None})

    elif type == "registration":
        try:
            application = Registration.get_by_id(id)
            if not application:
                raise AttributeError

            application.handled = not application.handled
            handled = application.handled
            db.session.commit()
        except AttributeError:
            return jsonify({"error": "Registration not found", "handled": None})

    return jsonify({"error": None, "handled": handled})


@admin.get("/applications/old/<type>/<int:page>")
@admin_required
def applications_old(type, page):
    if type == "toefl":
        toefl_applications = ToeflRegistration.get_pagination(page)
    elif type == "registration":
        toefl_applications = Registration.get_pagination(page)
    else:
        return redirect(url_for("admin.applications"))

    return render_template(
        "admin/applications_old.html",
        applications=toefl_applications,
        type=type,
        page=page,
    )


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
    "/course/timetable/add",
    view_func=AddTimetable.as_view("add_timetable"),
)
admin.add_url_rule(
    "/course/timetable/edit/<int:timetable_id>",
    view_func=EditTimetable.as_view("edit_timetable"),
)
admin.add_url_rule(
    "/course/timetable/delete/<int:timetable_id>",
    view_func=DeleteTimetable.as_view("delete_timetable"),
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


admin.add_url_rule("/feedback/add", view_func=AddFeedbackView.as_view("add_feedback"))
admin.add_url_rule(
    "/feedback/edit/<int:feedback_id>",
    view_func=EditFeedbackView.as_view("edit_feedback"),
)
admin.add_url_rule(
    "/feedback/delete/<int:feedback_id>",
    view_func=DeleteFeedbackView.as_view("delete_feedback"),
)
