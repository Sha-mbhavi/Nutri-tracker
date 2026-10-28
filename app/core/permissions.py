from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user


def admin_required(view):
    @wraps(view)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            flash("Administrator access required.", "error")
            return redirect(url_for("dashboard.dashboard"))
        return view(*args, **kwargs)
    return decorated_view
