from functools import wraps

from flask import redirect, url_for
from flask_login import current_user


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # if current_app.debug:
        #     return func(*args, **kwargs)
        if current_user.is_anonymous:
            return redirect(url_for("main.index"))
        if not current_user.is_admin:
            return redirect(url_for("main.index"))
        return func(*args, **kwargs)

    return wrapper
