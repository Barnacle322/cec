import datetime

from flask import flash, redirect, render_template, request, url_for
from flask.views import MethodView

from ..extenstions import db
from ..models import Event, EventType
from ..utils.decor import admin_required
from ..utils.status_enum import Status, StatusType


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
        if request.is_json:
            form_data = request.get_json()
        else:
            form_data = request.form

        name_ru = form_data.get("name_ru")
        name_en = form_data.get("name_en")
        name = {"ru": name_ru, "en": name_en or name_ru}

        description_ru = form_data.get("description_ru")
        description_en = form_data.get("description_en")
        description = {
            "ru": description_ru,
            "en": description_en or description_ru,
        }
        color = form_data.get("color")

        if not name or not description or not color:
            if request.is_json:
                return {"status": "error", "message": "Пожалуйста заполните все поля"}, 400
            status = Status(
                StatusType.ERROR, "Пожалуйста заполните все поля"
            ).get_status()

            return redirect(url_for("admin.add_event_type", _external=False, **status))

        try:
            event_type = EventType(_name=name, _description=description, color=color)
            db.session.add(event_type)
            db.session.commit()
        except Exception as e:
            if request.is_json:
                return {"status": "error", "message": f"Ошибка при создании типа события: {e}"}, 500
            status = Status(
                StatusType.ERROR, f"Ошибка при создании типа события: {e}"
            ).get_status()
            return redirect(url_for("admin.add_event_type", _external=False, **status))

        if request.is_json:
            return {"status": "success", "message": "Тип события добавлен успешно", "id": event_type.id, "name": event_type.name}, 200

        status = Status(StatusType.SUCCESS, "Тип события добавлен успешно").get_status()
        return redirect(url_for("admin.events", _external=False, **status))


class EditEventTypeView(MethodView):
    methods = ["GET", "POST"]

    @admin_required
    def get(self, event_type_id):
        event_type = EventType.get_by_id(event_type_id)
        if not event_type:
            status = Status(StatusType.ERROR, "Тип события не найден").get_status()
            return redirect(url_for("admin.events", _external=False, **status))
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
        colors.remove(event_type.color)
        return render_template(
            "admin/event/edit_event_type.html", event_type=event_type, colors=colors
        )

    @admin_required
    def post(self, event_type_id):
        form_data = request.form
        name_ru = form_data.get("name_ru")
        name_en = form_data.get("name_en")
        name = {"ru": name_ru, "en": name_en or name_ru}

        description_ru = form_data.get("description_ru")
        description_en = form_data.get("description_en")
        description = {
            "ru": description_ru,
            "en": description_en or description_ru,
        }
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
        form_data = request.form
        name_ru = form_data.get("name_ru")
        name_en = form_data.get("name_en")
        name = {"ru": name_ru, "en": name_en or name_ru}

        description_ru = form_data.get("description_ru")
        description_en = form_data.get("description_en")
        description = {
            "ru": description_ru,
            "en": description_en or description_ru,
        }

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
                _name=name,
                _description=description,
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
        form_data = request.form
        name_ru = form_data.get("name_ru")
        name_en = form_data.get("name_en")
        name = {"ru": name_ru, "en": name_en or name_ru}

        description_ru = form_data.get("description_ru")
        description_en = form_data.get("description_en")
        description = {
            "ru": description_ru,
            "en": description_en or description_ru,
        }
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
