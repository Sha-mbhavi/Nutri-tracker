from flask import Blueprint, render_template, request
from flask_login import login_required
from app.models import Recipe

recipes_bp = Blueprint("recipes", __name__, template_folder="templates")

@recipes_bp.route("/recipes")
@login_required
def recipes():
    ingredients = request.args.get("ingredients", "").strip().lower()
    recipes_query = Recipe.query
    if ingredients:
        recipes_query = recipes_query.filter(Recipe.ingredients.ilike(f"%{ingredients}%"))
    return render_template("recipes/recipes.html", recipes=recipes_query.all(), ingredients=ingredients)
