from flask import Blueprint, flash, render_template, request
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Goal

nutrition_bp = Blueprint("nutrition", __name__, template_folder="templates")


@nutrition_bp.route("/goals", methods=["GET", "POST"])
@login_required
def goals():
    if request.method == "POST":
        try:
            values = {field: float(request.form[field]) for field in ("target_calories", "target_protein", "target_carbs", "target_fat", "target_fiber", "target_water_ml")}
            if any(value < 0 for value in values.values()) or values["target_calories"] > 10000:
                raise ValueError
            Goal.query.filter_by(user_id=current_user.id, status="active").update({"status": "inactive"})
            db.session.add(Goal(user_id=current_user.id, **values))
            db.session.commit()
            flash("Goals saved.", "success")
        except (KeyError, TypeError, ValueError):
            db.session.rollback()
            flash("Please enter valid, non-negative targets.", "error")
    goal = Goal.query.filter_by(user_id=current_user.id, status="active").first()
    suggested = {"target_calories": 2000, "target_protein": 100, "target_carbs": 250,
                 "target_fat": 65, "target_fiber": 30, "target_water_ml": 2500}
    if current_user.profile and current_user.profile.nutrition_goal == "Lose weight":
        suggested["target_calories"] = 1800
    elif current_user.profile and current_user.profile.nutrition_goal == "Muscle gain":
        suggested["target_calories"] = 2200
        suggested["target_protein"] = 120
    return render_template("nutrition/goals.html", goal=goal, suggested=suggested)
