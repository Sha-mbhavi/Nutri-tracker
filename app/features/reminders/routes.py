from datetime import datetime
from flask import Blueprint, flash, render_template, request
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Reminder


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
    entries = Reminder.query.filter_by(user_id=current_user.id).all()
    return render_template("reminders/reminders.html", reminders=entries)
