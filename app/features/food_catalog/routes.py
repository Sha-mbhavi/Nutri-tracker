from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import func
from app.models import FoodCategory, FoodItem


food_catalog_bp = Blueprint("food_catalog", __name__, template_folder="templates")


@food_catalog_bp.route("/foods")
@login_required
def foods():
    query = request.args.get("q", "").strip()
    selected_category = request.args.get("category", "all").strip()

    categories = FoodCategory.query.filter_by(is_active=True).order_by(FoodCategory.id).all()
    foods_query = FoodItem.query.filter_by(is_active=True)

    if selected_category and selected_category.lower() != "all":
        if selected_category.isdigit():
            foods_query = foods_query.filter(FoodItem.category_id == int(selected_category))
        else:
            cat = FoodCategory.query.filter(func.lower(FoodCategory.name) == selected_category.lower()).first()
            if cat:
                foods_query = foods_query.filter(FoodItem.category_id == cat.id)
            else:
                foods_query = foods_query.filter(FoodItem.category_id == -1)

    if query:
        foods_query = foods_query.filter(FoodItem.name.ilike(f"%{query}%"))

    foods = foods_query.order_by(FoodItem.name).all()

    return render_template(
        "food_catalog/foods.html",
        foods=foods,
        categories=categories,
        selected_category=selected_category,
        query=query,
    )
