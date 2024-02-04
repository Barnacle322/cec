from functools import wraps

from flask import current_app, redirect, url_for
from flask_login import current_user


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_app.debug:
            return func(*args, **kwargs)
        if not current_user.is_authenticated or not current_user.is_admin:
            pass
            # return redirect(url_for("main.index"))
        return func(*args, **kwargs)

    return wrapper
