from datetime import date, timedelta
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from app.extensions import db
from app.models import PlannedMeal

planner_bp = Blueprint("planner", __name__, template_folder="templates")

@planner_bp.route("/planner", methods=["GET", "POST"])
@login_required
def planner():
    if request.method == "POST":
        try:
            planned_date = date.fromisoformat(request.form["planned_date"])
            meal_type = request.form["meal_type"]
            foods = request.form["foods"].strip()
            if meal_type not in {"Breakfast", "Lunch", "Dinner", "Snack"} or not foods:
                raise ValueError
            db.session.add(PlannedMeal(user_id=current_user.id, planned_date=planned_date,
                                       meal_type=meal_type, foods=foods))
            db.session.commit()
            flash("Meal planned.", "success")
            return redirect(url_for("planner.planner"))
        except (KeyError, ValueError):
            db.session.rollback()
            flash("Enter a valid meal plan.", "error")
    week_start = date.today() - timedelta(days=date.today().weekday())
    entries = PlannedMeal.query.filter_by(user_id=current_user.id).filter(
        PlannedMeal.planned_date >= week_start,
        PlannedMeal.planned_date <= week_start + timedelta(days=6)).order_by(PlannedMeal.planned_date).all()
    return render_template("planner/planner.html", entries=entries, week_start=week_start)
