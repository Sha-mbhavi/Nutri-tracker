from datetime import date
from flask import Blueprint, render_template
from flask_login import current_user, login_required
from .services import day_data, get_contribution_heatmap, get_daily_reminders_and_insights


dashboard_bp = Blueprint("dashboard", __name__, template_folder="templates")


@dashboard_bp.route("/")
def index():
    return render_template("dashboard/index.html")


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    totals, meals, goal = day_data(current_user.id, date.today())
    heatmap = get_contribution_heatmap(current_user.id, num_weeks=18)
    insights_data = get_daily_reminders_and_insights(current_user.id, date.today())

    # Calculate macro percentages
    total_macro_energy = (totals.get("protein", 0) * 4) + (totals.get("carbs", 0) * 4) + (totals.get("fat", 0) * 9)
    if total_macro_energy > 0:
        macro_pct = {
            "protein": round((totals["protein"] * 4 / total_macro_energy) * 100),
            "carbs": round((totals["carbs"] * 4 / total_macro_energy) * 100),
            "fat": round((totals["fat"] * 9 / total_macro_energy) * 100),
        }
    else:
        macro_pct = {"protein": 0, "carbs": 0, "fat": 0}

    return render_template(
        "dashboard/dashboard.html",
        totals=totals,
        meals=meals,
        goal=goal,
        heatmap=heatmap,
        macro_pct=macro_pct,
        insights_data=insights_data,
        suggestions=insights_data["bullet_insights"]
    )
