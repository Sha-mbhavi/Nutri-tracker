from datetime import date
from sqlalchemy import func
from app.core.nutrition import item_totals, round_nutrient
from app.extensions import db
from app.models import Goal, Meal, WaterIntake


def day_data(user_id, day):
    meals = Meal.query.filter_by(user_id=user_id, meal_date=day).all()
    meal_items = [item for meal in meals for item in meal.items]
    totals = item_totals(meal_items)
    water = db.session.query(func.coalesce(func.sum(WaterIntake.quantity_ml), 0)).filter(
        WaterIntake.user_id == user_id,
        func.date(WaterIntake.intake_datetime) == day,
    ).scalar()
    goal = Goal.query.filter_by(user_id=user_id, status="active").order_by(Goal.start_date.desc()).first()
    totals["water"] = round_nutrient(water)
    return totals, meals, goal
