import json
import time
from typing import Any

from flask import flash, redirect, render_template, request, url_for
from flask.views import MethodView

from ..extenstions import db
from ..models import Course, CourseGroup, Timetable
from ..utils.decor import admin_required
from ..utils.status_enum import Status, StatusType
from ..utils.storage import delete_blob_from_url, upload_picture


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
            return redirect(
                url_for("admin.add_course_group", _external=False, **status)
            )

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
                try:
                    delete_blob_from_url(course_group.picture_url)
                except Exception as e:
                    print(e)
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
        if not course:
            status = Status(StatusType.ERROR, "Курс не найден").get_status()
            return redirect(url_for("admin.courses", _external=False, **status))
        course_groups = list(CourseGroup.get_all())
        course_groups.remove(course.course_group)  # type: ignore

        return render_template(
            "admin/course/edit_course.html", course=course, course_groups=course_groups
        )

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
                try:
                    delete_blob_from_url(course.picture_url)
                except Exception as e:
                    print(e)
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


class AddTimetable(MethodView):
    methods = ["GET", "POST"]

    @admin_required
    def get(self):
        db_course = None
        if args := request.args:
            course_id = args.get("course_id", type=int)
            if course_id:
                db_course = Course.get_by_id(course_id)

        course_groups = CourseGroup.get_all_with_courses()

        return render_template(
            "admin/course/add_timetable.html",
            course_groups=course_groups,
            course_id=db_course.id if db_course else None,
        )

    @staticmethod
    def construct_timetable(form_data) -> dict[str, dict[str, Any]]:
        timetable = {
            "1": {
                "id": 1,
                "name": "Понедельник",
                "shorthand": "ПН",
                "time": None,
                "selected": False,
            },
            "2": {
                "id": 2,
                "name": "Вторник",
                "shorthand": "ВТ",
                "time": None,
                "selected": False,
            },
            "3": {
                "id": 3,
                "name": "Среда",
                "shorthand": "СР",
                "time": None,
                "selected": False,
            },
            "4": {
                "id": 4,
                "name": "Четверг",
                "shorthand": "ЧТ",
                "time": None,
                "selected": False,
            },
            "5": {
                "id": 5,
                "name": "Пятница",
                "shorthand": "ПТ",
                "time": None,
                "selected": False,
            },
            "6": {
                "id": 6,
                "name": "Суббота",
                "shorthand": "СБ",
                "time": None,
                "selected": False,
            },
            "7": {
                "id": 7,
                "name": "Воскресенье",
                "shorthand": "ВС",
                "time": None,
                "selected": False,
            },
        }

        if monday := form_data.get("monday"):
            day = timetable["1"]
            day["time"] = monday
            day["selected"] = True
        if tuesday := form_data.get("tuesday"):
            day = timetable["2"]
            day["time"] = tuesday
            day["selected"] = True
        if wednesday := form_data.get("wednesday"):
            day = timetable["3"]
            day["time"] = wednesday
            day["selected"] = True
        if thursday := form_data.get("thursday"):
            day = timetable["4"]
            day["time"] = thursday
            day["selected"] = True
        if friday := form_data.get("friday"):
            day = timetable["5"]
            day["time"] = friday
            day["selected"] = True
        if saturday := form_data.get("saturday"):
            day = timetable["6"]
            day["time"] = saturday
            day["selected"] = True
        if sunday := form_data.get("sunday"):
            day = timetable["7"]
            day["time"] = sunday
            day["selected"] = True

        return timetable

    @admin_required
    def post(self):
        name = request.form.get("name")
        description = request.form.get("description")
        duration = request.form.get("duration")
        price = request.form.get("price")
        course_id = request.form.get("course_id", type=int)

        timetable = AddTimetable.construct_timetable(request.form)

        if not name or not description or not duration or not price or not course_id:
            status = Status(
                StatusType.ERROR, "Пожалуйста заполните все поля"
            ).get_status()

            return redirect(url_for("admin.add_timetable", _external=False, **status))

        try:
            new_timetable = Timetable(
                name=name,
                description=description,
                duration=duration,
                price=price,
                json_data=timetable,  # type: ignore
                course_id=course_id,
            )
            db.session.add(new_timetable)
            db.session.commit()
        except Exception as e:
            status = Status(
                StatusType.ERROR, f"Ошибка при создании расписания: {e}"
            ).get_status()
            return redirect(url_for("admin.add_timetable", _external=False, **status))

        return redirect(url_for("admin.add_timetable"))


class EditTimetable(MethodView):
    methods = ["GET", "POST"]

    @admin_required
    def get(self, timetable_id):
        timetable = Timetable.get_by_id(timetable_id)
        course_groups = CourseGroup.get_all_with_courses()

        return render_template(
            "admin/course/edit_timetable.html",
            timetable=timetable,
            course_groups=course_groups,
        )

    @admin_required
    def post(self, timetable_id):
        name = request.form.get("name")
        description = request.form.get("description")
        duration = request.form.get("duration")
        price = request.form.get("price")
        course_id = request.form.get("course_id", type=int)

        timetable_data = AddTimetable.construct_timetable(request.form)

        if not name or not description or not duration or not price or not course_id:
            status = Status(
                StatusType.ERROR, "Пожалуйста заполните все поля"
            ).get_status()

            return redirect(url_for("admin.edit_timetable", _external=False, **status))

        try:
            timetable = Timetable.get_by_id(timetable_id)
            if not timetable:
                raise Exception("Timetable not found")
            timetable.name = name
            timetable.description = description
            timetable.duration = duration
            timetable.price = price
            timetable.json_data = timetable_data  # type: ignore
            timetable.course_id = course_id
            db.session.commit()
        except Exception as e:
            status = Status(
                StatusType.ERROR, f"Ошибка при редактировании расписания: {e}"
            ).get_status()
            return redirect(url_for("admin.edit_timetable", _external=False, **status))

        return redirect(url_for("admin.courses"))


class DeleteTimetable(MethodView):
    methods = ["POST"]

    @admin_required
    def post(self, timetable_id):
        try:
            Timetable.delete_by_id(timetable_id)
        except Exception as e:
            flash(f"Error deleting timetable: {e}", "danger")
            return redirect(url_for("admin.courses"))

        flash("Timetable deleted successfully", "success")
        return redirect(url_for("admin.courses"))
