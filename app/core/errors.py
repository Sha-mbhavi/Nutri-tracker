from flask import flash, redirect, url_for


def register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(_error):
        flash("Access denied.", "error")
        return redirect(url_for("dashboard.dashboard")), 403
