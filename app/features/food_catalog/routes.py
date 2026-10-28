from flask import Blueprint, render_template, request
from flask_login import login_required
from app.models import FoodItem


food_catalog_bp = Blueprint("food_catalog", __name__, template_folder="templates")


@food_catalog_bp.route("/foods")
@login_required
def foods():
    query = request.args.get("q", "").strip()
    foods_query = FoodItem.query.filter_by(is_active=True)
    if query:
        foods_query = foods_query.filter(FoodItem.name.ilike(f"%{query}%"))
    return render_template("food_catalog/foods.html", foods=foods_query.all(), query=query)
