from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Reminder
from app.features.dashboard.services import get_daily_reminders_and_insights


reminders_bp = Blueprint("reminders", __name__, template_folder="templates")


@reminders_bp.route("/reminders", methods=["GET", "POST"])
@login_required
def reminders():
    if request.method == "POST":
        try:
            reminder_time = datetime.strptime(request.form["reminder_time"], "%H:%M").time()
            db.session.add(Reminder(user_id=current_user.id, reminder_type=request.form["reminder_type"],
                                    title=request.form["title"].strip(), reminder_time=reminder_time,
                                    repeat_rule=request.form.get("repeat_rule", "Daily")))
            db.session.commit()
            flash("Reminder created.", "success")
        except (KeyError, ValueError):
            db.session.rollback()
            flash("Enter a valid reminder.", "error")
        return redirect(url_for("reminders.reminders"))

    entries = Reminder.query.filter_by(user_id=current_user.id).all()
    insights_data = get_daily_reminders_and_insights(current_user.id)
    return render_template("reminders/reminders.html", reminders=entries, insights_data=insights_data)


@reminders_bp.route("/reminders/<int:reminder_id>/toggle", methods=["POST"])
@login_required
def toggle_reminder(reminder_id):
    reminder = Reminder.query.filter_by(id=reminder_id, user_id=current_user.id).first_or_404()
    reminder.is_active = not reminder.is_active
    db.session.commit()
    flash(f"Reminder updated.", "success")
    return redirect(url_for("reminders.reminders"))


@reminders_bp.route("/reminders/<int:reminder_id>/delete", methods=["POST"])
@login_required
def delete_reminder(reminder_id):
    reminder = Reminder.query.filter_by(id=reminder_id, user_id=current_user.id).first_or_404()
    db.session.delete(reminder)
    db.session.commit()
    flash("Reminder deleted.", "success")
    return redirect(url_for("reminders.reminders"))
