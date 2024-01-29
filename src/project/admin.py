from flask import Blueprint, render_template

from .models import CourseGroup, EventType, Staff, Teacher
from .utils.decor import admin_required
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
def toefl():
    return render_template("admin/toefl.html")


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
