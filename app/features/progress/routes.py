from datetime import date
from flask import Blueprint, flash, render_template, request
from flask_login import current_user, login_required
from app.extensions import db
from app.models import WeightLog

progress_bp = Blueprint("progress", __name__, template_folder="templates")

@progress_bp.route("/progress", methods=["GET", "POST"])
@login_required
def progress():
    if request.method == "POST":
        try:
            weight = float(request.form["weight_kg"])
            measured_on = date.fromisoformat(request.form.get("measured_on") or date.today().isoformat())
            if not 1 <= weight <= 500 or measured_on > date.today():
                raise ValueError
            db.session.add(WeightLog(user_id=current_user.id, weight_kg=weight, measured_on=measured_on))
            db.session.commit()
            flash("Weight recorded.", "success")
        except (KeyError, TypeError, ValueError):
            db.session.rollback()
            flash("Enter a valid weight and measurement date.", "error")
    entries = WeightLog.query.filter_by(user_id=current_user.id).order_by(WeightLog.measured_on.asc()).all()
    height = current_user.profile.height_cm / 100 if current_user.profile and current_user.profile.height_cm else None
    weight = entries[-1].weight_kg if entries else (current_user.profile.weight_kg if current_user.profile else None)
    bmi = round(weight / (height * height), 1) if height and weight else None
    return render_template("progress/progress.html", entries=entries, bmi=bmi)

@progress_bp.route("/bmi")
@login_required
def bmi():
    profile = current_user.profile
    height = profile.height_cm / 100 if profile and profile.height_cm else None
    weight = profile.weight_kg if profile else None
    value = round(weight / (height * height), 1) if height and weight else None
    return render_template("progress/bmi.html", height=height, weight=weight, bmi=value)
