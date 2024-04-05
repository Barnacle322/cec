from flask import flash, redirect, render_template, request, url_for
from flask.views import MethodView

from ..extenstions import db
from ..models import Staff, Teacher
from ..utils.decor import admin_required
from ..utils.status_enum import Status, StatusType
from ..utils.storage import delete_blob_from_url, upload_picture


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
                try:
                    delete_blob_from_url(picture_url)
                except Exception as e:
                    print(f"Error deleting picture: {e}")
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
                try:
                    delete_blob_from_url(teacher.picture_url)
                except Exception as e:
                    print(f"Error deleting picture: {e}")
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
                try:
                    delete_blob_from_url(picture_url)
                except Exception as e:
                    print(f"Error deleting picture: {e}")
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
                try:
                    delete_blob_from_url(staff.picture_url)
                except Exception as e:
                    print(f"Error deleting picture: {e}")
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
