from datetime import date, timedelta
from flask import Blueprint, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import func
from app.extensions import db
from app.features.dashboard.services import day_data
from app.models import Meal, MealItem, WaterIntake, WeightLog

analytics_bp = Blueprint("analytics", __name__, template_folder="templates")

@analytics_bp.route("/analytics")
@login_required
def analytics():
    period = request.args.get("period", "7")
    days = 30 if period == "30" else 7
    start = date.today() - timedelta(days=days - 1)
    rows = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        totals, meals, _ = day_data(current_user.id, day)
        rows.append({"date": day.isoformat(), "label": day.strftime("%d %b"), **totals, "meals": len(meals)})
    averages = {key: round(sum(row[key] for row in rows) / days, 1) if rows else 0 for key in ("calories", "protein", "carbs", "fat", "water")}
    weights = WeightLog.query.filter_by(user_id=current_user.id).filter(WeightLog.measured_on >= start).order_by(WeightLog.measured_on).all()
    return render_template("analytics/analytics.html", rows=rows, averages=averages, period=period, weights=weights)
