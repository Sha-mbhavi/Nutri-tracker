from datetime import date, timedelta
from flask import Blueprint, render_template
from flask_login import current_user, login_required
from .services import day_data


dashboard_bp = Blueprint("dashboard", __name__, template_folder="templates")


@dashboard_bp.route("/")
def index():
    return render_template("dashboard/index.html")


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    totals, meals, goal = day_data(current_user.id, date.today())
    week = []
    for offset in range(6, -1, -1):
        day = date.today() - timedelta(days=offset)
        day_totals, _, _ = day_data(current_user.id, day)
        week.append({"date": day.strftime("%a"), "calories": day_totals["calories"]})
    suggestions = []
    if goal:
        remaining = max(goal.target_calories - totals["calories"], 0)
        if remaining > 100:
            suggestions.append(f"You have about {round(remaining)} calories remaining today.")
        if totals["water"] < goal.target_water_ml:
            suggestions.append("A few glasses of water can help reach your hydration target.")
    else:
        suggestions.append("Set your daily goals to receive personalized wellness guidance.")
    return render_template("dashboard/dashboard.html", totals=totals, meals=meals, goal=goal, week=week, suggestions=suggestions)
