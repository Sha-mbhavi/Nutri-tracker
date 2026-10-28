from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, logout_user
from app.extensions import db
from app.models import UserSettings

account_bp = Blueprint("account", __name__, template_folder="templates")

@account_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.session.add(settings)
        db.session.commit()
    if request.method == "POST":
        settings.meal_reminders_enabled = request.form.get("meal_reminders") == "on"
        settings.water_reminders_enabled = request.form.get("water_reminders") == "on"
        try:
            settings.reminder_interval_minutes = max(15, min(1440, int(request.form.get("interval", 120))))
        except ValueError:
            settings.reminder_interval_minutes = 120
        db.session.commit()
        flash("Settings saved.", "success")
    return render_template("account/settings.html", settings=settings)

@account_bp.route("/account/delete", methods=["POST"])
@login_required
def delete_account():
    if request.form.get("confirm") != "DELETE":
        flash("Type DELETE to confirm account removal.", "error")
        return redirect(url_for("account.settings"))
    user = current_user._get_current_object()
    logout_user()
    db.session.delete(user)
    db.session.commit()
    flash("Your account and related records were deleted.", "success")
    return redirect(url_for("dashboard.index"))
