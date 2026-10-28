from datetime import date
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from app.extensions import db
from app.models import ActivityLog, FoodItem, Meal, MealItem
from app.features.dashboard.services import day_data


meals_bp = Blueprint("meals", __name__, template_folder="templates")


@meals_bp.route("/meals", methods=["GET", "POST"])
@login_required
def meals():
    if request.method == "POST":
        try:
            food_id = int(request.form["food_id"])
            quantity = float(request.form["quantity"])
            meal_type = request.form["meal_type"]
            if quantity <= 0 or meal_type not in {"Breakfast", "Lunch", "Dinner", "Snack"}:
                raise ValueError
            meal = Meal.query.filter_by(user_id=current_user.id, meal_date=date.today(), meal_type=meal_type).first()
            if not meal:
                meal = Meal(user_id=current_user.id, meal_type=meal_type, meal_date=date.today())
                db.session.add(meal)
                db.session.flush()
            db.session.add(MealItem(meal_id=meal.id, food_id=food_id, quantity=quantity, unit="g"))
            db.session.add(ActivityLog(user_id=current_user.id, action="meal_item_added", details=f"Food {food_id}, quantity {quantity}g"))
            db.session.commit()
            flash("Meal item saved.", "success")
            return redirect(url_for("meals.meals"))
        except (KeyError, ValueError):
            db.session.rollback()
            flash("Enter a valid food and quantity greater than zero.", "error")
    totals, _, _ = day_data(current_user.id, date.today())
    return render_template("meals/meals.html",
        meals=Meal.query.filter_by(user_id=current_user.id, meal_date=date.today()).all(),
        foods=FoodItem.query.filter_by(is_active=True).order_by(FoodItem.name).all(), totals=totals)


@meals_bp.route("/meals/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_meal_item(item_id):
    item = MealItem.query.join(Meal).filter(MealItem.id == item_id, Meal.user_id == current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Meal item deleted.", "success")
    return redirect(url_for("meals.meals"))


@meals_bp.route("/meals/<int:meal_id>/duplicate", methods=["POST"])
@login_required
def duplicate_meal(meal_id):
    source = Meal.query.filter_by(id=meal_id, user_id=current_user.id).first_or_404()
    meal = Meal(user_id=current_user.id, meal_date=date.today(), meal_type=source.meal_type)
    db.session.add(meal)
    db.session.flush()
    for source_item in source.items:
        db.session.add(MealItem(meal_id=meal.id, food_id=source_item.food_id,
                                quantity=source_item.quantity, unit=source_item.unit))
    db.session.commit()
    flash("Meal duplicated for today.", "success")
    return redirect(url_for("meals.meals"))
