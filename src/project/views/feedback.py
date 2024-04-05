import datetime

from flask import flash, redirect, render_template, request, url_for
from flask.views import MethodView

from ..extenstions import db
from ..models import Feedback
from ..utils.decor import admin_required
from ..utils.status_enum import Status, StatusType
from ..utils.storage import upload_picture


class AddFeedbackView(MethodView):
    methods = ["GET", "POST"]

    @admin_required
    def get(self):
        return render_template("admin/feedback/add_feedback.html")

    @admin_required
    def post(self):
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        number = request.form.get("number")
        picture = request.files.get("picture")
        course = request.form.get("course")
        created_at = request.form.get("created_at")

        if not name or not message:
            status = Status(
                StatusType.ERROR, "Пожалуйста заполните все поля"
            ).get_status()

            return redirect(url_for("admin.add_feedback", _external=False, **status))

        try:
            feedback = Feedback(name=name, message=message)
            if picture:
                feedback.picture_url = upload_picture(picture)
            if course:
                feedback.course = course
            if email:
                feedback.email = email
            if number:
                feedback.number = number
            if created_at:
                feedback.created_at = datetime.datetime.strptime(created_at, "%Y-%m-%d")
            else:
                feedback.created_at = datetime.date.today()

            db.session.add(feedback)
            db.session.commit()
        except Exception as e:
            status = Status(
                StatusType.ERROR, f"Ошибка при создании отзыва: {e}"
            ).get_status()
            return redirect(url_for("admin.add_feedback", _external=False, **status))

        status = Status(StatusType.SUCCESS, "Отзыв добавлен успешно").get_status()
        return redirect(url_for("admin.feedback", _external=False, **status))


class EditFeedbackView(MethodView):
    methods = ["GET", "POST"]

    @admin_required
    def get(self, feedback_id):
        feedback = Feedback.get_by_id(feedback_id)
        return render_template("admin/feedback/edit_feedback.html", feedback=feedback)

    @admin_required
    def post(self, feedback_id):
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        number = request.form.get("number")
        picture = request.files.get("picture")
        course = request.form.get("course")
        created_at = request.form.get("created_at")

        if not name or not message:
            status = Status(
                StatusType.ERROR, "Пожалуйста заполните все поля"
            ).get_status()

            return redirect(
                url_for(
                    "admin.edit_feedback",
                    feedback_id=feedback_id,
                    _external=False,
                    **status,
                )
            )

        try:
            feedback = Feedback.get_by_id(feedback_id)
            if not feedback:
                raise Exception("Feedback not found")
            feedback.name = name
            feedback.message = message
            if picture:
                feedback.picture_url = upload_picture(picture)
            if course:
                feedback.course = course
            if email:
                feedback.email = email
            if number:
                feedback.number = number
            if created_at:
                feedback.created_at = datetime.datetime.strptime(created_at, "%Y-%m-%d")
            else:
                feedback.created_at = datetime.date.today()

            db.session.commit()
        except Exception as e:
            status = Status(
                StatusType.ERROR, f"Ошибка при редактировании отзыва: {e}"
            ).get_status()
            return redirect(
                url_for(
                    "admin.edit_feedback",
                    feedback_id=feedback_id,
                    _external=False,
                    **status,
                )
            )

        status = Status(StatusType.SUCCESS, "Отзыв отредактирован успешно").get_status()
        return redirect(url_for("admin.feedbacks", _external=False, **status))


class DeleteFeedbackView(MethodView):
    methods = ["POST"]

    @admin_required
    def post(self, feedback_id):
        try:
            Feedback.delete_by_id(feedback_id)
        except Exception as e:
            flash(f"Error deleting feedback: {e}", "danger")
            return redirect(url_for("admin.feedbacks"))

        flash("Feedback deleted successfully", "success")
        return redirect(url_for("admin.feedbacks"))
