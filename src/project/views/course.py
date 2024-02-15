from flask import flash, redirect, render_template, request, url_for
from flask.views import MethodView

from ..extenstions import db
from ..models import Course, CourseGroup
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
        if not course:
            status = Status(StatusType.ERROR, "Курс не найден").get_status()
            return redirect(url_for("admin.courses", _external=False, **status))
        course_groups = list(CourseGroup.get_all())
        course_groups.remove(course.course_group)

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
