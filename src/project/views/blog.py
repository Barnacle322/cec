from flask import redirect, render_template, request, url_for
from flask.views import MethodView

from ..extenstions import db
from ..models import Blog
from ..utils.decor import admin_required
from ..utils.status_enum import Status, StatusType


class EditBlogView(MethodView):
    methods = ["GET", "POST"]

    @admin_required
    def get(self, blog_id):
        blog = Blog.get_by_id(blog_id)
        if not blog:
            return redirect(url_for("admin.blogs"))

        return render_template("admin/blog/create_blog.html", title=blog.title)

    @admin_required
    def post(self, blog_id):
        form_data = request.get_json()
        blog = Blog.get_by_id(blog_id)
        if not blog:
            return redirect(url_for("admin.blogs"))

        title = form_data.get("title")
        if blog.title != title:
            blog.title = title
            blog.set_title(value=title)

        blog.json = form_data.get("data")

        db.session.commit()

        status = Status(StatusType.SUCCESS, "Блог добавлен успешно").get_status()
        return redirect(url_for("admin.courses", _external=False, **status))


# class DeleteCourseView(MethodView):
#     methods = ["POST"]

#     @admin_required
#     def post(self, course_id):
#         try:
#             Course.delete_by_id(course_id)
#         except Exception as e:
#             flash(f"Error deleting course: {e}", "danger")
#             return redirect(url_for("admin.courses"))

#         flash("Course deleted successfully", "success")
#         return redirect(url_for("admin.courses"))
