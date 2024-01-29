import datetime
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask.views import MethodView
from flask_login import current_user

from .extenstions import db
from .models import Course, CourseGroup, Event, EventType, Staff, Teacher
from .utils.status_enum import Status, StatusType
from .utils.storage import delete_blob_from_url, upload_picture

admin = Blueprint("admin", __name__)


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # if not current_user.is_authenticated or not current_user.is_admin:
        #     return redirect(url_for("main.index"))
        return func(*args, **kwargs)

    return wrapper


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


class AddTeacherView(MethodView):
    methods = ["GET", "POST"]

    @admin_required
    def get(self):
        return render_template("admin/people/add_teacher.html")

    @admin_required
    def post(self):
        name = request.form.get("name")
        description = request.form.get("description")
        bio = request.form.get("bio")
        picture = request.files.get("picture")

        if not name or not description or not picture or not bio:
            status = Status(
                StatusType.ERROR, "Пожалуйста заполните все поля"
            ).get_status()

            return redirect(url_for("admin.add_teacher", _external=False, **status))
        try:
            picture_url = upload_picture(picture)
        except Exception as e:
            status = Status(
                StatusType.ERROR, f"Ошибка при загрузке изображения: {e}"
            ).get_status()
            return redirect(url_for("admin.add_teacher", _external=False, **status))

        try:
            teacher = Teacher(
                name=name, description=description, bio=bio, picture_url=picture_url
            )
            db.session.add(teacher)
            db.session.commit()
        except Exception as e:
            status = Status(
                StatusType.ERROR, f"Ошибка при создании учителя: {e}"
            ).get_status()
            if picture_url:
                delete_blob_from_url(picture_url)
            return redirect(url_for("admin.add_teacher", _external=False, **status))

        status = Status(StatusType.SUCCESS, "Учитель добавлен успешно").get_status()
        return redirect(url_for("admin.people", _external=False, **status))


class EditTeacherView(MethodView):
    methods = ["GET", "POST"]

    @admin_required
    def get(self, teacher_id):
        teacher = Teacher.get_by_id(teacher_id)
        return render_template("admin/people/edit_teacher.html", teacher=teacher)

    @admin_required
    def post(self, teacher_id):
        name = request.form.get("name")
        description = request.form.get("description")
        bio = request.form.get("bio")
        picture = request.files.get("picture")

        if not name or not description or not bio:
            status = Status(
                StatusType.ERROR, "Пожалуйста заполните все поля"
            ).get_status()

            return redirect(
                url_for(
                    "admin.edit_teacher",
                    teacher_id=teacher_id,
                    _external=False,
                    **status,
                )
            )

        try:
            teacher = Teacher.get_by_id(teacher_id)
            if not teacher:
                raise Exception("Teacher not found")
            teacher.name = name
            teacher.description = description
            teacher.bio = bio
            if picture:
                picture_url = upload_picture(picture)
                delete_blob_from_url(teacher.picture_url)
                teacher.picture_url = picture_url
            db.session.commit()
        except Exception as e:
            status = Status(
                StatusType.ERROR, f"Ошибка при редактировании учителя: {e}"
            ).get_status()
            return redirect(
                url_for(
                    "admin.edit_teacher",
                    teacher_id=teacher_id,
                    _external=False,
                    **status,
                )
            )

        status = Status(
            StatusType.SUCCESS, "Учитель отредактирован успешно"
        ).get_status()
        return redirect(url_for("admin.people", _external=False, **status))


class DeleteTeacherView(MethodView):
    methods = ["POST"]

    @admin_required
    def post(self, teacher_id):
        try:
            Teacher.delete_by_id(teacher_id)
        except Exception as e:
            flash(f"Error deleting teacher: {e}", "danger")
            return redirect(url_for("admin.people"))

        flash("Teacher deleted successfully", "success")
        return redirect(url_for("admin.people"))


class AddStaffView(MethodView):
    methods = ["GET", "POST"]

    @admin_required
    def get(self):
        return render_template("admin/people/add_staff.html")

    @admin_required
    def post(self):
        name = request.form.get("name")
        description = request.form.get("description")
        picture = request.files.get("picture")

        if not name or not description or not picture:
            status = Status(
                StatusType.ERROR, "Пожалуйста заполните все поля"
            ).get_status()

            return redirect(url_for("admin.add_staff", _external=False, **status))

        try:
            picture_url = upload_picture(picture)
        except Exception as e:
            status = Status(
                StatusType.ERROR, f"Ошибка при загрузке изображения: {e}"
            ).get_status()
            return redirect(url_for("admin.add_staff", _external=False, **status))

        try:
            staff = Staff(name=name, description=description, picture_url=picture_url)
            db.session.add(staff)
            db.session.commit()
        except Exception as e:
            status = Status(
                StatusType.ERROR, f"Ошибка при создании сотрудника: {e}"
            ).get_status()
            if picture_url:
                delete_blob_from_url(picture_url)
            return redirect(url_for("admin.add_staff", _external=False, **status))

        status = Status(StatusType.SUCCESS, "Сотрудник добавлен успешно").get_status()
        return redirect(url_for("admin.people", _external=False, **status))


class EditStaffView(MethodView):
    methods = ["GET", "POST"]

    @admin_required
    def get(self, staff_id):
        staff = Staff.get_by_id(staff_id)
        return render_template("admin/people/edit_staff.html", staff=staff)

    @admin_required
    def post(self, staff_id):
        name = request.form.get("name")
        description = request.form.get("description")
        picture = request.files.get("picture")

        if not name or not description:
            status = Status(
                StatusType.ERROR, "Пожалуйста заполните все поля"
            ).get_status()

            return redirect(
                url_for(
                    "admin.edit_staff",
                    staff_id=staff_id,
                    _external=False,
                    **status,
                )
            )

        try:
            staff = Staff.get_by_id(staff_id)
            if not staff:
                raise Exception("Staff not found")
            staff.name = name
            staff.description = description
            if picture:
                picture_url = upload_picture(picture)
                delete_blob_from_url(staff.picture_url)
                staff.picture_url = picture_url
            db.session.commit()
        except Exception as e:
            status = Status(
                StatusType.ERROR, f"Ошибка при редактировании сотрудника: {e}"
            ).get_status()
            return redirect(
                url_for(
                    "admin.edit_staff",
                    staff_id=staff_id,
                    _external=False,
                    **status,
                )
            )

        status = Status(
            StatusType.SUCCESS, "Сотрудник отредактирован успешно"
        ).get_status()
        return redirect(url_for("admin.people", _external=False, **status))


class DeleteStaffView(MethodView):
    methods = ["POST"]

    @admin_required
    def post(self, staff_id):
        try:
            Staff.delete_by_id(staff_id)
        except Exception as e:
            flash(f"Error deleting staff: {e}", "danger")
            return redirect(url_for("admin.people"))

        flash("Staff deleted successfully", "success")
        return redirect(url_for("admin.people"))


class AddCourseGroupView(MethodView):
    methods = ["GET", "POST"]

    @admin_required
    def get(self):
        return render_template("admin/course/add_course_group.html")

    @admin_required
    def post(self):
        name = request.form.get("name")
        description = request.form.get("description")
        link = request.form.get("link")
        picture = request.files.get("picture")

        if not name or not description or not link or not picture:
            status = Status(
                StatusType.ERROR, "Пожалуйста заполните все поля"
            ).get_status()

            return redirect(
                url_for("admin.add_course_group", _external=False, **status)
            )

        try:
            picture_url = upload_picture(picture)
        except Exception as e:
            status = Status(
                StatusType.ERROR, f"Ошибка при загрузке изображения: {e}"
            ).get_status()
            return redirect(url_for("admin.add_staff", _external=False, **status))

        try:
            course_group = CourseGroup(
                name=name, description=description, link=link, picture_url=picture_url
            )
            db.session.add(course_group)
            db.session.commit()
        except Exception as e:
            status = Status(
                StatusType.ERROR, f"Ошибка при создании группы курсов: {e}"
            ).get_status()
            return redirect(
                url_for("admin.add_course_group", _external=False, **status)
            )

        status = Status(
            StatusType.SUCCESS, "Группа курсов добавлена успешно"
        ).get_status()
        return redirect(url_for("admin.courses", _external=False, **status))


class EditCourseGroupView(MethodView):
    methods = ["GET", "POST"]

    @admin_required
    def get(self, course_group_id):
        course_group = CourseGroup.get_by_id(course_group_id)
        return render_template(
            "admin/course/edit_course_group.html", course_group=course_group
        )

    @admin_required
    def post(self, course_group_id):
        name = request.form.get("name")
        description = request.form.get("description")
        link = request.form.get("link")
        picture = request.files.get("picture")

        if not name or not description or not link:
            status = Status(
                StatusType.ERROR, "Пожалуйста заполните все поля"
            ).get_status()

            return redirect(
                url_for(
                    "admin.edit_course_group",
                    course_group_id=course_group_id,
                    _external=False,
                    **status,
                )
            )

        try:
            course_group = CourseGroup.get_by_id(course_group_id)
            if not course_group:
                raise Exception("Course group not found")
            course_group.name = name
            course_group.description = description
            course_group.link = link
            if picture:
                picture_url = upload_picture(picture)
                delete_blob_from_url(course_group.picture_url)
                course_group.picture_url = picture_url
            db.session.commit()
        except Exception as e:
            status = Status(
                StatusType.ERROR, f"Ошибка при редактировании группы курсов: {e}"
            ).get_status()
            return redirect(
                url_for(
                    "admin.edit_course_group",
                    course_group_id=course_group_id,
                    _external=False,
                    **status,
                )
            )

        status = Status(
            StatusType.SUCCESS, "Группа курсов отредактирована успешно"
        ).get_status()
        return redirect(url_for("admin.courses", _external=False, **status))


class DeleteCourseGroupView(MethodView):
    methods = ["POST"]

    @admin_required
    def post(self, course_group_id):
        try:
            CourseGroup.delete_by_id(course_group_id)
        except Exception as e:
            flash(f"Error deleting course group: {e}", "danger")
            return redirect(url_for("admin.courses"))

        flash("Course group deleted successfully", "success")
        return redirect(url_for("admin.courses"))


class AddCourseView(MethodView):
    methods = ["GET", "POST"]

    @admin_required
    def get(self):
        course_groups = list(CourseGroup.get_all())
        course_group = None
        if course_group_id := request.args.get("course_group_id", type=int):
            course_group = CourseGroup.get_by_id(course_group_id)
            if course_group:
                course_groups.remove(course_group)

        return render_template(
            "admin/course/add_course.html",
            course_group=course_group,
            course_groups=course_groups,
        )

    @admin_required
    def post(
        self,
    ):
        name = request.form.get("name")
        description = request.form.get("description")
        link = request.form.get("link")
        course_group_id = request.form.get("course_group_id")
        picture = request.files.get("picture")

        if (
            not name
            or not description
            or not link
            or not picture
            or not course_group_id
        ):
            status = Status(
                StatusType.ERROR, "Пожалуйста заполните все поля"
            ).get_status()

            return redirect(
                url_for(
                    "admin.add_course",
                    course_group_id=course_group_id,
                    _external=False,
                    **status,
                )
            )

        try:
            picture_url = upload_picture(picture)
        except Exception as e:
            status = Status(
                StatusType.ERROR, f"Ошибка при загрузке изображения: {e}"
            ).get_status()
            return redirect(
                url_for(
                    "admin.add_course",
                    course_group_id=course_group_id,
                    _external=False,
                    **status,
                )
            )

        try:
            course = Course(
                name=name,
                description=description,
                link=link,
                picture_url=picture_url,
                course_group_id=course_group_id,
            )
            db.session.add(course)
            db.session.commit()
        except Exception as e:
            status = Status(
                StatusType.ERROR, f"Ошибка при создании курса: {e}"
            ).get_status()
            return redirect(
                url_for(
                    "admin.add_course",
                    course_group_id=course_group_id,
                    _external=False,
                    **status,
                )
            )

        status = Status(StatusType.SUCCESS, "Курс добавлен успешно").get_status()
        return redirect(url_for("admin.courses", _external=False, **status))


class EditCourseView(MethodView):
    methods = ["GET", "POST"]

    @admin_required
    def get(self, course_id):
        course = Course.get_by_id(course_id)
        return render_template("admin/course/edit_course.html", course=course)

    @admin_required
    def post(self, course_id):
        name = request.form.get("name")
        description = request.form.get("description")
        link = request.form.get("link")
        picture = request.files.get("picture")

        if not name or not description or not link:
            status = Status(
                StatusType.ERROR, "Пожалуйста заполните все поля"
            ).get_status()

            return redirect(
                url_for(
                    "admin.edit_course",
                    course_id=course_id,
                    _external=False,
                    **status,
                )
            )

        try:
            course = Course.get_by_id(course_id)
            if not course:
                raise Exception("Course not found")
            course.name = name
            course.description = description
            course.link = link
            if picture:
                picture_url = upload_picture(picture)
                delete_blob_from_url(course.picture_url)
                course.picture_url = picture_url
            db.session.commit()
        except Exception as e:
            status = Status(
                StatusType.ERROR, f"Ошибка при редактировании курса: {e}"
            ).get_status()
            return redirect(
                url_for(
                    "admin.edit_course",
                    course_id=course_id,
                    _external=False,
                    **status,
                )
            )

        status = Status(StatusType.SUCCESS, "Курс отредактирован успешно").get_status()
        return redirect(url_for("admin.courses", _external=False, **status))


class DeleteCourseView(MethodView):
    methods = ["POST"]

    @admin_required
    def post(self, course_id):
        try:
            Course.delete_by_id(course_id)
        except Exception as e:
            flash(f"Error deleting course: {e}", "danger")
            return redirect(url_for("admin.courses"))

        flash("Course deleted successfully", "success")
        return redirect(url_for("admin.courses"))


class AddEventTypeView(MethodView):
    methods = ["GET", "POST"]

    @admin_required
    def get(self):
        colors = [
            "neutral-300",
            "red-300",
            "orange-300",
            "amber-300",
            "yellow-300",
            "lime-300",
            "green-300",
            "emerald-300",
            "teal-300",
            "cyan-300",
            "sky-300",
            "blue-300",
            "indigo-300",
            "violet-300",
            "purple-300",
            "fuchsia-300",
            "pink-300",
            "rose-300",
        ]
        return render_template("admin/event/add_event_type.html", colors=colors)

    @admin_required
    def post(self):
        name = request.form.get("name")
        description = request.form.get("description")
        color = request.form.get("color")

        if not name or not description or not color:
            status = Status(
                StatusType.ERROR, "Пожалуйста заполните все поля"
            ).get_status()

            return redirect(url_for("admin.add_event_type", _external=False, **status))

        try:
            event_type = EventType(name=name, description=description, color=color)
            db.session.add(event_type)
            db.session.commit()
        except Exception as e:
            status = Status(
                StatusType.ERROR, f"Ошибка при создании типа события: {e}"
            ).get_status()
            return redirect(url_for("admin.add_event_type", _external=False, **status))

        status = Status(StatusType.SUCCESS, "Тип события добавлен успешно").get_status()
        return redirect(url_for("admin.events", _external=False, **status))


class EditEventTypeView(MethodView):
    methods = ["GET", "POST"]

    @admin_required
    def get(self, event_type_id):
        event_type = EventType.get_by_id(event_type_id)
        colors = [
            "neutral-300",
            "red-300",
            "orange-300",
            "amber-300",
            "yellow-300",
            "lime-300",
            "green-300",
            "emerald-300",
            "teal-300",
            "cyan-300",
            "sky-300",
            "blue-300",
            "indigo-300",
            "violet-300",
            "purple-300",
            "fuchsia-300",
            "pink-300",
            "rose-300",
        ]
        return render_template(
            "admin/event/edit_event_type.html", event_type=event_type, colors=colors
        )

    @admin_required
    def post(self, event_type_id):
        name = request.form.get("name")
        description = request.form.get("description")
        color = request.form.get("color")

        if not name or not description or not color:
            status = Status(
                StatusType.ERROR, "Пожалуйста заполните все поля"
            ).get_status()

            return redirect(
                url_for(
                    "admin.edit_event_type",
                    event_type_id=event_type_id,
                    _external=False,
                    **status,
                )
            )

        try:
            event_type = EventType.get_by_id(event_type_id)
            if not event_type:
                raise Exception("Event type not found")
            event_type.name = name
            event_type.description = description
            event_type.color = color
            db.session.commit()
        except Exception as e:
            status = Status(
                StatusType.ERROR, f"Ошибка при редактировании типа события: {e}"
            ).get_status()
            return redirect(
                url_for(
                    "admin.edit_event_type",
                    event_type_id=event_type_id,
                    _external=False,
                    **status,
                )
            )

        status = Status(
            StatusType.SUCCESS, "Тип события отредактирован успешно"
        ).get_status()
        return redirect(url_for("admin.events", _external=False, **status))


class DeleteEventTypeView(MethodView):
    methods = ["POST"]

    @admin_required
    def post(self, event_type_id):
        try:
            EventType.delete_by_id(event_type_id)
        except Exception as e:
            flash(f"Error deleting event type: {e}", "danger")
            return redirect(url_for("admin.events"))

        flash("Event type deleted successfully", "success")
        return redirect(url_for("admin.events"))


class AddEventView(MethodView):
    methods = ["GET", "POST"]

    @admin_required
    def get(self):
        event_type = None
        event_types = list(EventType.get_all())
        if event_type_id := request.args.get("event_type_id", type=int):
            event_type = EventType.get_by_id(event_type_id)
            if event_type:
                event_types.remove(event_type)

        return render_template(
            "admin/event/add_event.html", event_type=event_type, event_types=event_types
        )

    @admin_required
    def post(self):
        name = request.form.get("name")
        description = request.form.get("description")
        event_type_id = request.form.get("event_type_id", type=int)
        date_str = request.form.get("date")

        if not name or not description or not event_type_id or not date_str:
            status = Status(
                StatusType.ERROR, "Пожалуйста заполните все поля"
            ).get_status()

            return redirect(url_for("admin.add_event", _external=False, **status))

        date = datetime.datetime.strptime(date_str, "%Y-%m-%d")

        try:
            event_type = EventType.get_by_id(event_type_id)
            if not event_type:
                raise Exception("Event type not found")
            event = Event(
                name=name,
                description=description,
                event_type_id=event_type_id,
                date=date,
            )
            db.session.add(event)
            db.session.commit()
        except Exception as e:
            status = Status(
                StatusType.ERROR, f"Ошибка при создании события: {e}"
            ).get_status()
            return redirect(url_for("admin.add_event", _external=False, **status))

        status = Status(StatusType.SUCCESS, "Событие добавлено успешно").get_status()
        return redirect(url_for("admin.events", _external=False, **status))


class EditEventView(MethodView):
    methods = ["GET", "POST"]

    @admin_required
    def get(self, event_id):
        event = Event.get_by_id(event_id)
        event_types = EventType.get_all()
        return render_template(
            "admin/event/edit_event.html", event=event, event_types=event_types
        )

    @admin_required
    def post(self, event_id):
        name = request.form.get("name")
        description = request.form.get("description")
        event_type_id = request.form.get("event_type_id", type=int)
        date_str = request.form.get("date")

        if not name or not description or not event_type_id or not date_str:
            status = Status(
                StatusType.ERROR, "Пожалуйста заполните все поля"
            ).get_status()

            return redirect(
                url_for(
                    "admin.edit_event",
                    event_id=event_id,
                    _external=False,
                    **status,
                )
            )

        date = datetime.datetime.strptime(date_str, "%Y-%m-%d")

        try:
            event = Event.get_by_id(event_id)
            if not event:
                raise Exception("Event not found")
            event.name = name
            event.description = description
            event.event_type_id = event_type_id
            event.date = date
            db.session.commit()
        except Exception as e:
            status = Status(
                StatusType.ERROR, f"Ошибка при редактировании события: {e}"
            ).get_status()
            return redirect(
                url_for(
                    "admin.edit_event",
                    event_id=event_id,
                    _external=False,
                    **status,
                )
            )

        status = Status(
            StatusType.SUCCESS, "Событие отредактировано успешно"
        ).get_status()
        return redirect(url_for("admin.events", _external=False, **status))


class DeleteEventView(MethodView):
    methods = ["POST"]

    @admin_required
    def post(self, event_id):
        try:
            Event.delete_by_id(event_id)
        except Exception as e:
            flash(f"Error deleting event: {e}", "danger")
            return redirect(url_for("admin.events"))

        flash("Event deleted successfully", "success")
        return redirect(url_for("admin.events"))


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
