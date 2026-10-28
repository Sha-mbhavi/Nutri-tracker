from datetime import date
from flask import Blueprint, render_template
from flask_login import current_user, login_required
from app.features.dashboard.services import day_data
from app.models import FoodItem, Goal

suggestions_bp = Blueprint("suggestions", __name__, template_folder="templates")

@suggestions_bp.route("/suggestions")
@login_required
def suggestions():
    totals, _, goal = day_data(current_user.id, date.today())
    target = goal.target_calories if goal else 2000
    protein_target = goal.target_protein if goal else 100
    remaining_protein = max(protein_target - totals["protein"], 0)
    foods = FoodItem.query.filter_by(is_active=True).order_by(FoodItem.protein.desc(), FoodItem.name).all()
    allergies = (current_user.profile.food_allergies or "").lower() if current_user.profile else ""
    diet = (current_user.profile.diet_preference or "").lower() if current_user.profile else ""
    suitable = []
    for food in foods:
        text = food.name.lower()
        if allergies and any(item.strip() in text for item in allergies.split(",") if item.strip()):
            continue
        if diet == "vegan" and food.name.lower() in {"chicken breast", "greek yogurt"}:
            continue
        if diet == "vegetarian" and "chicken" in text:
            continue
        suitable.append(food)
    suitable = sorted(suitable, key=lambda food: food.protein, reverse=True)[:8]
    return render_template("suggestions/suggestions.html", foods=suitable, remaining_protein=remaining_protein,
                           remaining_calories=max(target - totals["calories"], 0))
