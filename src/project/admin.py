import csv
import datetime
import os

import requests
from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from lxml import html
from xlsx2csv import Xlsx2csv

from .extenstions import db
from .models import (
    Blog,
    CourseGroup,
    Event,
    Feedback,
    Registration,
    Staff,
    Teacher,
    Timetable,
    Toefl,
    ToeflRegistration,
    User,
)
from .utils.decor import admin_required
from .utils.status_enum import Status, StatusType
from .utils.storage import upload_picture
from .views.blog import EditBlogView
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
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@admin.route("/courses")
@admin_required
def courses():
    status_type, msg = None, None
    if query := request.args:
        status_type = query.get("type")
        msg = query.get("msg")

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
        status_type=status_type,
        msg=msg,
    )


@admin.route("/courses/<int:course_id>", methods=["POST"])
@admin_required
def edit_timetable_positions(course_id):
    if request.method == "POST":
        timetables = Timetable.get_all()

        request_data = request.json
        positions = {int(item.get("id")): item.get("position") for item in request_data}  # type: ignore
        for timetable in timetables:
            if timetable.course_id == course_id:
                new_position = positions.get(timetable.id)
                if (
                    new_position is not None
                    and timetable.course_position != new_position
                ):
                    timetable.course_position = new_position
                    db.session.add(timetable)
        db.session.commit()
    return jsonify({"status": "success"}, 200)


@admin.route("/events")
@admin_required
def events():
    status_type, msg = None, None
    if query := request.args:
        status_type = query.get("type")
        msg = query.get("msg")

    upcoming_events = Event.get_upcoming()
    past_events = Event.get_past()
    return render_template(
        "admin/events.html",
        upcoming_events=upcoming_events,
        past_events=past_events,
        status_type=status_type,
        msg=msg,
    )


@admin.route("/people")
@admin_required
def people():
    status_type, msg = None, None
    if query := request.args:
        status_type = query.get("type")
        msg = query.get("msg")

    teachers = Teacher.get_all()
    staff = Staff.get_all()
    return render_template(
        "admin/people/people.html",
        teachers=teachers,
        staff=staff,
        status_type=status_type,
        msg=msg,
    )


@admin.route("/toefl")
@admin_required
def toefl():
    status_type, msg = None, None
    if query := request.args:
        status_type = query.get("type")
        msg = query.get("msg")

    if (
        date_str := request.args.get("date", type=str)
    ) != "None" and date_str is not None:
        try:
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            human_date = date.strftime("%d %B, %Y")
            results = Toefl.get_all_by_date(date)
        except ValueError:
            date = datetime.date.today()
            human_date = date.strftime("%d %B, %Y")
            results = Toefl.get_latest_results()
    else:
        results = Toefl.get_latest_results()
        date = results[0].date if results else datetime.date.today()
        human_date = date.strftime("%d %B, %Y")

    pagination = Toefl.get_pagination_dates(date)
    return render_template(
        "admin/toefl.html",
        pagination=pagination,
        results=results,
        human_date=human_date,
        status_type=status_type,
        msg=msg,
    )


@admin.route("/toefl/add", methods=["GET", "POST"])
@admin_required
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
            file_path = os.path.join(BASE_DIR, "static", "toefl", "toefl.xlsx")
            csv_path = os.path.join(BASE_DIR, "static", "toefl", "toefl.csv")
            file.save(file_path)
            Xlsx2csv(file_path, outputencoding="utf-8").convert(csv_path)
            os.remove(file_path)

            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f, dialect="excel")
                header = [x.upper().strip() for x in reader.fieldnames if x != ""]  # type: ignore
                if header != ["ID", "LISTENING", "GRAMMAR", "READING"]:
                    status = Status(
                        StatusType.ERROR,
                        "Неверный формат файла. Первая строка должна содержать заголовки столбцов: ID, LISTENING, GRAMMAR, READING",
                    ).get_status()
                    return redirect(url_for("admin.toefl", _external=False, **status))

                toefl_results = []
                Toefl.delete_by_date(date)
                for line in reader:
                    if line and any(line.values()):
                        try:
                            del line[""]
                        except KeyError:
                            pass
                        toefl_results.append(
                            Toefl(
                                test_taker_id=line.get("ID", "NO ID"),
                                listening=int(line.get("LISTENING", 0)),
                                grammar=int(line.get("GRAMMAR", 0)),
                                reading=int(line.get("READING", 0)),
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
    status_type, msg = None, None
    if query := request.args:
        status_type = query.get("type")
        msg = query.get("msg")

    feedbacks = Feedback.get_all()
    return render_template(
        "admin/feedback.html", feedbacks=feedbacks, status_type=status_type, msg=msg
    )


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

            if not toefl.handled:
                toefl.handled = True
                toefl.handled_at = datetime.datetime.now(tz=datetime.timezone.utc)
            else:
                toefl.handled = False
                toefl.handled_at = None

            handled = toefl.handled
            db.session.commit()
        except AttributeError:
            return jsonify({"error": "TOEFL registration not found", "handled": None})

    elif type == "registration":
        try:
            application = Registration.get_by_id(id)
            if not application:
                raise AttributeError

            if not application.handled:
                application.handled = True
                application.handled_at = datetime.datetime.now(tz=datetime.timezone.utc)
            else:
                application.handled = False
                application.handled_at = None

            handled = application.handled
            db.session.commit()
        except AttributeError:
            return jsonify({"error": "Registration not found", "handled": None})

    return jsonify({"error": None, "handled": handled})


@admin.post("/applications/bulk_archive")
@admin_required
def bulk_archive():
    data = request.get_json()
    if not data or "items" not in data:
        return jsonify({"error": "Invalid request data"}), 400

    items = data.get("items", [])
    archived_count = 0
    errors = []

    for item in items:
        item_type = item.get("type")
        item_id = item.get("id")

        if not item_type or not item_id:
            continue

        try:
            if item_type == "toefl":
                application = ToeflRegistration.get_by_id(int(item_id))
                if application:
                    application.handled = True
                    application.handled_at = datetime.datetime.now(
                        tz=datetime.timezone.utc
                    )
                    archived_count += 1
            elif item_type == "registration":
                application = Registration.get_by_id(int(item_id))
                if application:
                    application.handled = True
                    application.handled_at = datetime.datetime.now(
                        tz=datetime.timezone.utc
                    )
                    archived_count += 1
        except Exception as e:
            errors.append({"type": item_type, "id": item_id, "error": str(e)})

    db.session.commit()

    return jsonify(
        {"success": True, "archived_count": archived_count, "errors": errors}
    )


@admin.post("/applications/archive_old")
@admin_required
def archive_old_applications():
    # Archive applications older than 30 days
    cutoff_date = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(
        days=30
    )

    # Get old unhandled registration applications
    old_registrations = (
        db.session.query(Registration)
        .filter(Registration.handled.is_(False), Registration.created_at < cutoff_date)
        .all()
    )

    # Get old unhandled TOEFL applications
    old_toefl = (
        db.session.query(ToeflRegistration)
        .filter(
            ToeflRegistration.handled.is_(False),
            ToeflRegistration.created_at < cutoff_date,
        )
        .all()
    )

    # Archive them
    for app in old_registrations:
        app.handled = True
        app.handled_at = datetime.datetime.now(tz=datetime.timezone.utc)

    for app in old_toefl:
        app.handled = True
        app.handled_at = datetime.datetime.now(tz=datetime.timezone.utc)

    db.session.commit()

    return jsonify(
        {
            "success": True,
            "archived_count": len(old_registrations) + len(old_toefl),
            "registrations": len(old_registrations),
            "toefl": len(old_toefl),
        }
    )


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


@admin.get("/blogs")
@admin_required
def blogs():
    blogs = Blog.get_all()
    return render_template("admin/blogs.html", blogs=blogs)


@admin.get("/blog/create")
@admin_required
def create_blog():
    new_blog = Blog()
    new_blog.set_title(value="Новый блог")
    db.session.add(new_blog)
    db.session.commit()

    return redirect(url_for("admin.edit_blog", blog_id=new_blog.id))


@admin.get("/blog/data/<int:blog_id>")
@admin_required
def get_blog_data(blog_id):
    blog = Blog.get_by_id(blog_id)
    if not blog:
        return jsonify(message="Blog not found"), 404
    return jsonify(blog.json)


@admin.route("/blog/image/upload", methods=["POST"])
@admin_required
def upload_image():
    try:
        if "image" not in request.files:
            return jsonify(message="No file part"), 400
        file = request.files["image"]
        if file.filename == "":
            return jsonify(message="No selected file"), 400
        picture_url = upload_picture(file)
        return jsonify(success=1, file={"url": picture_url}), 200
    except Exception as e:
        return jsonify(message=str(e)), 500


@admin.route("/blog/image/fetch", methods=["POST"])
@admin_required
def fetch_image():
    try:
        data = request.get_json()
        url = data.get("url")
        return jsonify(success=1, file={"url": url}), 200
    except Exception as e:
        return jsonify(message=str(e)), 500


@admin.route("/blog/link", methods=["GET"])
@admin_required
def fetch_url():
    url = request.args.get("url")
    if url is None:
        return jsonify(detail="URL parameter is required"), 400

    try:
        response = requests.get(url)
        tree = html.fromstring(response.content)

        title = tree.findtext(".//title")

        description = tree.xpath('//meta[@name="description"]/@content')
        description = description[0] if description else None

        image = tree.xpath('//meta[@property="og:image"]/@content')
        image = image[0] if image else None

        return jsonify(
            success=1,
            link=url,
            meta={
                "title": title,
                "description": description,
                "image": {"url": image},
            },
        ), 200
    except Exception as e:
        return jsonify(message=str(e)), 500


@admin.post("/blog/publish-status/<int:id>")
@admin_required
def change_publish_status(id: int):
    blog = Blog.get_by_id(id)
    if not blog:
        return jsonify(message="Blog not found"), 404

    request_data = request.get_json()
    blog.is_draft = request_data.get("is_draft")

    db.session.commit()
    return redirect(url_for("admin.edit_blog", blog_id=id))


@admin.get("/create_admin")
@admin_required
def member():
    return render_template("admin/member.html")


@admin.post("/create_admin")
@admin_required
def create_member():
    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        return redirect(url_for("admin.member"))

    user = User.get_by_username(username)
    if user:
        return redirect(url_for("admin.member"))

    user = User(username=username, password=password)
    db.session.add(user)
    db.session.commit()

    return redirect(url_for("admin.member"))


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


admin.add_url_rule(
    "/blog/edit/<int:blog_id>", view_func=EditBlogView.as_view("edit_blog")
)
