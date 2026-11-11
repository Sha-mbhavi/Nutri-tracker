import os
from datetime import date, datetime, time, timedelta
import random
from flask import Flask
from sqlalchemy import inspect, text

from config import Config
from .extensions import db, login_manager
from .models import (
    ActivityLog,
    FoodCategory,
    FoodItem,
    Goal,
    Meal,
    MealItem,
    Profile,
    Recipe,
    User,
    WaterIntake,
    WeightLog,
)
from .core.errors import register_error_handlers


# Standardized 7-Category Curated Food Catalog (56 items across 7 distinct categories)
CATALOG_DATA = {
    "Whole Grains & Staples": [
        ("Brown Rice", "100g", 123.0, 2.7, 25.6, 1.0, 1.6),
        ("Rolled Oats", "100g", 389.0, 16.9, 66.3, 6.9, 10.6),
        ("Quinoa", "100g", 120.0, 4.4, 21.3, 1.9, 2.8),
        ("Chapati", "100g", 120.0, 3.4, 24.0, 1.1, 2.3),
        ("Sweet Potato", "100g", 86.0, 1.6, 20.1, 0.1, 3.0),
        ("Sourdough Bread", "100g", 230.0, 8.5, 46.0, 1.2, 2.4),
        ("Wild Rice", "100g", 101.0, 4.0, 21.3, 0.3, 1.8),
        ("Buckwheat", "100g", 149.0, 5.7, 30.6, 1.0, 2.7),
    ],
    "Lean Proteins": [
        ("Chicken Breast", "100g", 165.0, 31.0, 0.0, 3.6, 0.0),
        ("Salmon Fillet", "100g", 208.0, 20.4, 0.0, 13.4, 0.0),
        ("Whole Egg", "100g", 143.0, 12.6, 0.7, 9.5, 0.0),
        ("Egg White", "100g", 52.0, 10.9, 0.7, 0.2, 0.0),
        ("Turkey Breast", "100g", 135.0, 30.0, 0.0, 1.0, 0.0),
        ("Tuna (in water)", "100g", 116.0, 26.0, 0.0, 1.0, 0.0),
        ("Cod Fillet", "100g", 82.0, 17.8, 0.0, 0.7, 0.0),
        ("Shrimp", "100g", 99.0, 24.0, 0.2, 0.3, 0.0),
    ],
    "Vegetables & Greens": [
        ("Broccoli", "100g", 34.0, 2.8, 6.6, 0.4, 2.6),
        ("Baby Spinach", "100g", 23.0, 2.9, 3.6, 0.4, 2.2),
        ("Curly Kale", "100g", 49.0, 4.3, 8.8, 0.9, 3.6),
        ("Bell Pepper", "100g", 31.0, 1.0, 6.0, 0.3, 2.1),
        ("Carrots", "100g", 41.0, 0.9, 9.6, 0.2, 2.8),
        ("Cucumber", "100g", 15.0, 0.7, 3.6, 0.1, 0.5),
        ("Asparagus", "100g", 20.0, 2.2, 3.9, 0.1, 2.1),
        ("Mushrooms", "100g", 22.0, 3.1, 3.3, 0.3, 1.0),
        ("Zucchini", "100g", 17.0, 1.2, 3.1, 0.3, 1.0),
        ("Cauliflower", "100g", 25.0, 1.9, 5.0, 0.3, 2.0),
    ],
    "Fruits & Berries": [
        ("Banana", "100g", 89.0, 1.1, 22.8, 0.3, 2.6),
        ("Apple", "100g", 52.0, 0.3, 13.8, 0.2, 2.4),
        ("Blueberries", "100g", 57.0, 0.7, 14.5, 0.3, 2.4),
        ("Strawberries", "100g", 32.0, 0.7, 7.7, 0.3, 2.0),
        ("Orange", "100g", 47.0, 0.9, 11.8, 0.1, 2.4),
        ("Avocado", "100g", 160.0, 2.0, 8.5, 14.7, 6.7),
        ("Kiwi", "100g", 61.0, 1.1, 14.7, 0.5, 3.0),
        ("Pomegranate", "100g", 83.0, 1.7, 18.7, 1.2, 4.0),
    ],
    "Plant Proteins & Legumes": [
        ("Dal", "100g", 116.0, 9.0, 20.0, 0.8, 7.9),
        ("Chickpeas", "100g", 164.0, 8.9, 27.4, 2.6, 7.6),
        ("Firm Tofu", "100g", 144.0, 17.3, 2.8, 8.7, 2.3),
        ("Tempeh", "100g", 192.0, 20.3, 7.6, 10.8, 9.0),
        ("Edamame", "100g", 121.0, 11.9, 8.9, 5.2, 5.2),
        ("Black Beans", "100g", 132.0, 8.9, 23.7, 0.5, 8.7),
        ("Kidney Beans", "100g", 127.0, 8.7, 22.8, 0.5, 6.4),
        ("Green Peas", "100g", 81.0, 5.4, 14.5, 0.4, 5.7),
    ],
    "Dairy & Cultured": [
        ("Greek Yogurt", "100g", 59.0, 10.0, 3.6, 0.4, 0.0),
        ("Paneer", "100g", 265.0, 18.0, 1.2, 20.0, 0.0),
        ("Cottage Cheese", "100g", 98.0, 11.1, 3.4, 4.3, 0.0),
        ("Skim Milk", "100g", 35.0, 3.4, 5.0, 0.1, 0.0),
        ("Unsweetened Soy Milk", "100g", 33.0, 3.3, 1.8, 1.6, 0.6),
        ("Unsweetened Almond Milk", "100g", 15.0, 0.6, 0.3, 1.2, 0.2),
        ("Whey Protein Isolate", "100g", 370.0, 85.0, 3.0, 1.5, 0.0),
    ],
    "Nuts, Seeds & Healthy Fats": [
        ("Raw Almonds", "100g", 579.0, 21.2, 21.6, 49.9, 12.5),
        ("Walnuts", "100g", 654.0, 15.2, 13.7, 65.2, 6.7),
        ("Chia Seeds", "100g", 486.0, 16.5, 42.1, 30.7, 34.4),
        ("Flax Seeds", "100g", 534.0, 18.3, 28.9, 42.2, 27.3),
        ("Natural Peanut Butter", "100g", 588.0, 25.1, 20.0, 50.4, 6.0),
        ("Extra Virgin Olive Oil", "100g", 884.0, 0.0, 0.0, 100.0, 0.0),
        ("Pumpkin Seeds", "100g", 559.0, 30.2, 10.7, 49.1, 6.0),
    ],
}


def seed_data():
    """Seeds the 7 food categories and 50+ diverse whole foods."""
    # Ensure all 7 distinct categories exist
    category_map = {}
    for cat_name in CATALOG_DATA.keys():
        category = FoodCategory.query.filter_by(name=cat_name).first()
        if not category:
            category = FoodCategory(name=cat_name)
            db.session.add(category)
            db.session.flush()
        category_map[cat_name] = category

    # Reassign any legacy category 'Staples' foods to correct categories
    legacy = FoodCategory.query.filter_by(name="Staples").first()
    if legacy:
        mapping = {
            "Brown Rice": category_map["Whole Grains & Staples"].id,
            "Chapati": category_map["Whole Grains & Staples"].id,
            "Chicken Breast": category_map["Lean Proteins"].id,
            "Banana": category_map["Fruits & Berries"].id,
            "Broccoli": category_map["Vegetables & Greens"].id,
            "Greek Yogurt": category_map["Dairy & Cultured"].id,
            "Paneer": category_map["Dairy & Cultured"].id,
            "Dal": category_map["Plant Proteins & Legumes"].id,
            "Chickpeas": category_map["Plant Proteins & Legumes"].id,
        }
        for fname, cid in mapping.items():
            db.session.execute(
                text("UPDATE food_item SET category_id = :cid WHERE name = :name"),
                {"cid": cid, "name": fname},
            )
        db.session.execute(text("DELETE FROM food_category WHERE name = 'Staples'"))
        db.session.commit()

    for cat_name, items in CATALOG_DATA.items():
        cat = category_map[cat_name]
        for name, basis, calories, protein, carbs, fat, fiber in items:
            food = FoodItem.query.filter_by(name=name).first()
            if not food:
                db.session.add(
                    FoodItem(
                        category_id=cat.id,
                        name=name,
                        serving_basis=basis,
                        calories=calories,
                        protein=protein,
                        carbs=carbs,
                        fat=fat,
                        fiber=fiber,
                    )
                )
            else:
                food.category_id = cat.id
                food.serving_basis = basis
                food.calories = calories
                food.protein = protein
                food.carbs = carbs
                food.fat = fat
                food.fiber = fiber
    db.session.commit()


def seed_recipes():
    if Recipe.query.first():
        return
    db.session.add_all([
        Recipe(name="Dal and brown rice bowl", ingredients="dal, brown rice, onion, tomato, spices", instructions="Cook dal, prepare rice, combine with warm spices and herbs.", dietary_tags="Vegetarian"),
        Recipe(name="Paneer vegetable stir-fry", ingredients="paneer, broccoli, bell pepper, olive oil", instructions="Saute vegetables in olive oil, add cubed paneer, season and serve.", dietary_tags="Vegetarian"),
        Recipe(name="Mediterranean chickpea bowl", ingredients="chickpeas, spinach, cucumber, olive oil", instructions="Toss chickpeas with spinach, cucumber and light vinaigrette.", dietary_tags="Vegan"),
    ])
    db.session.commit()


def seed_users():
    """
    Seeds demo user and admin accounts with rich historical logs for the GitHub heatmap.
    """
    user = User.query.filter_by(email="user@nutritrack.com").first()
    if not user:
        user = User(name="Sample User", email="user@nutritrack.com", role="user", is_active=True)
        user.set_password("User123!")
        db.session.add(user)
        db.session.flush()

        profile = Profile(
            user_id=user.id,
            date_of_birth=date(1998, 5, 20),
            height_cm=175.0,
            weight_kg=72.0,
            activity_level="Moderate",
            diet_preference="Balanced",
            food_allergies="None",
            nutrition_goal="Maintenance"
        )
        db.session.add(profile)

        goal = Goal(
            user_id=user.id,
            target_calories=2100.0,
            target_protein=125.0,
            target_carbs=230.0,
            target_fat=60.0,
            target_fiber=30.0,
            target_water_ml=2500.0,
            start_date=date.today() - timedelta(days=90),
            status="active"
        )
        db.session.add(goal)
        db.session.flush()

    # Seed 12-week (84 days) historical logging if user has few entries or needs intensity calibration
    existing_meals_count = Meal.query.filter_by(user_id=user.id).count()
    needs_history = False
    if existing_meals_count < 50:
        needs_history = True
    else:
        from app.features.dashboard.services import get_contribution_heatmap
        hm = get_contribution_heatmap(user.id)
        levels_present = {d["level"] for w in hm["weeks"] for d in w if not d["is_future"]}
        if 3 not in levels_present or len(levels_present) < 5:
            needs_history = True

    if needs_history:
        # Clean existing meal items, meals, water, weight for demo user
        meal_ids = [m.id for m in Meal.query.filter_by(user_id=user.id).all()]
        if meal_ids:
            MealItem.query.filter(MealItem.meal_id.in_(meal_ids)).delete(synchronize_session=False)
            Meal.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        WaterIntake.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        WeightLog.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        db.session.flush()

        chicken = FoodItem.query.filter_by(name="Chicken Breast").first() or FoodItem.query.first()
        rice = FoodItem.query.filter_by(name="Brown Rice").first() or FoodItem.query.first()
        oats = FoodItem.query.filter_by(name="Rolled Oats").first() or FoodItem.query.first()
        banana = FoodItem.query.filter_by(name="Banana").first() or FoodItem.query.first()
        eggs = FoodItem.query.filter_by(name="Whole Egg").first() or FoodItem.query.first()
        yogurt = FoodItem.query.filter_by(name="Greek Yogurt").first() or FoodItem.query.first()
        salmon = FoodItem.query.filter_by(name="Salmon Fillet").first() or FoodItem.query.first()
        broccoli = FoodItem.query.filter_by(name="Broccoli").first() or FoodItem.query.first()
        almonds = FoodItem.query.filter_by(name="Raw Almonds").first() or FoodItem.query.first()
        sweet_potato = FoodItem.query.filter_by(name="Sweet Potato").first() or FoodItem.query.first()
        avocado = FoodItem.query.filter_by(name="Avocado").first() or FoodItem.query.first()
        olive_oil = FoodItem.query.filter_by(name="Extra Virgin Olive Oil").first() or FoodItem.query.first()
        berries = FoodItem.query.filter_by(name="Blueberries").first() or FoodItem.query.first()
        asparagus = FoodItem.query.filter_by(name="Asparagus").first() or FoodItem.query.first()

        # Seed 84 days (12 weeks) of varied meals, hydration, and weight progression
        today = date.today()
        rng = random.Random(42)  # Deterministic seed for consistency
        current_weight = 75.2

        for offset in range(83, -1, -1):
            day = today - timedelta(days=offset)
            # Cycle through realistic habits: 0 to 4 meals
            if offset == 0:
                num_meals = 3
            elif offset == 1:
                num_meals = 3
            elif offset == 2:
                num_meals = 4
            elif offset == 3:
                num_meals = 2
            elif offset == 4:
                num_meals = 3
            elif offset == 5:
                num_meals = 3
            elif offset == 6:
                num_meals = 0
            else:
                day_type = rng.random()
                if day_type < 0.08:
                    num_meals = 0  # Rest / missed logging day (Level 0)
                elif day_type < 0.22:
                    num_meals = 1  # Light snack day (Level 1, <35% target)
                elif day_type < 0.45:
                    num_meals = 2  # Partial day (Level 2, 35-70% target)
                elif day_type < 0.85:
                    num_meals = 3  # Standard balanced target achieved (Level 4, 70-115% target)
                else:
                    num_meals = 4  # High intake / surplus workout day (Level 3, >115% target)

            if num_meals == 1:
                # Level 1: Light day (~220 kcal < 735 kcal threshold)
                m1 = Meal(user_id=user.id, meal_date=day, meal_time=time(11, 0), meal_type="Snack")
                db.session.add(m1)
                db.session.flush()
                db.session.add(MealItem(meal_id=m1.id, food_id=yogurt.id, quantity=150.0, unit="g"))
                db.session.add(MealItem(meal_id=m1.id, food_id=banana.id, quantity=100.0, unit="g"))
                if berries:
                    db.session.add(MealItem(meal_id=m1.id, food_id=berries.id, quantity=60.0, unit="g"))

            elif num_meals == 2:
                # Level 2: Partial day (~860 kcal, between 735 and 1470 kcal)
                m1 = Meal(user_id=user.id, meal_date=day, meal_time=time(8, 30), meal_type="Breakfast")
                db.session.add(m1)
                db.session.flush()
                db.session.add(MealItem(meal_id=m1.id, food_id=oats.id, quantity=60.0, unit="g"))
                db.session.add(MealItem(meal_id=m1.id, food_id=banana.id, quantity=100.0, unit="g"))
                db.session.add(MealItem(meal_id=m1.id, food_id=yogurt.id, quantity=100.0, unit="g"))

                m2 = Meal(user_id=user.id, meal_date=day, meal_time=time(13, 0), meal_type="Lunch")
                db.session.add(m2)
                db.session.flush()
                db.session.add(MealItem(meal_id=m2.id, food_id=chicken.id, quantity=150.0, unit="g"))
                db.session.add(MealItem(meal_id=m2.id, food_id=rice.id, quantity=140.0, unit="g"))
                db.session.add(MealItem(meal_id=m2.id, food_id=broccoli.id, quantity=100.0, unit="g"))

            elif num_meals == 3:
                # Level 4: Target Achieved (~1580-1700 kcal, between 1470 and 2415 kcal)
                m1 = Meal(user_id=user.id, meal_date=day, meal_time=time(8, 30), meal_type="Breakfast")
                db.session.add(m1)
                db.session.flush()
                db.session.add(MealItem(meal_id=m1.id, food_id=oats.id, quantity=70.0, unit="g"))
                db.session.add(MealItem(meal_id=m1.id, food_id=banana.id, quantity=100.0, unit="g"))
                if eggs:
                    db.session.add(MealItem(meal_id=m1.id, food_id=eggs.id, quantity=100.0, unit="g"))

                m2 = Meal(user_id=user.id, meal_date=day, meal_time=time(13, 0), meal_type="Lunch")
                db.session.add(m2)
                db.session.flush()
                db.session.add(MealItem(meal_id=m2.id, food_id=chicken.id, quantity=160.0, unit="g"))
                db.session.add(MealItem(meal_id=m2.id, food_id=rice.id, quantity=160.0, unit="g"))
                db.session.add(MealItem(meal_id=m2.id, food_id=broccoli.id, quantity=100.0, unit="g"))
                if olive_oil:
                    db.session.add(MealItem(meal_id=m2.id, food_id=olive_oil.id, quantity=10.0, unit="g"))

                m3 = Meal(user_id=user.id, meal_date=day, meal_time=time(19, 30), meal_type="Dinner")
                db.session.add(m3)
                db.session.flush()
                db.session.add(MealItem(meal_id=m3.id, food_id=salmon.id if salmon else chicken.id, quantity=160.0, unit="g"))
                if sweet_potato:
                    db.session.add(MealItem(meal_id=m3.id, food_id=sweet_potato.id, quantity=180.0, unit="g"))
                else:
                    db.session.add(MealItem(meal_id=m3.id, food_id=rice.id, quantity=140.0, unit="g"))
                if asparagus:
                    db.session.add(MealItem(meal_id=m3.id, food_id=asparagus.id, quantity=100.0, unit="g"))

            elif num_meals == 4:
                # Level 3: Surplus / High Workout Day (~2650 kcal >= 2415 kcal)
                m1 = Meal(user_id=user.id, meal_date=day, meal_time=time(8, 0), meal_type="Breakfast")
                db.session.add(m1)
                db.session.flush()
                db.session.add(MealItem(meal_id=m1.id, food_id=oats.id, quantity=100.0, unit="g"))
                db.session.add(MealItem(meal_id=m1.id, food_id=banana.id, quantity=120.0, unit="g"))
                if eggs:
                    db.session.add(MealItem(meal_id=m1.id, food_id=eggs.id, quantity=150.0, unit="g"))

                m2 = Meal(user_id=user.id, meal_date=day, meal_time=time(12, 45), meal_type="Lunch")
                db.session.add(m2)
                db.session.flush()
                db.session.add(MealItem(meal_id=m2.id, food_id=chicken.id, quantity=220.0, unit="g"))
                db.session.add(MealItem(meal_id=m2.id, food_id=rice.id, quantity=220.0, unit="g"))
                db.session.add(MealItem(meal_id=m2.id, food_id=broccoli.id, quantity=100.0, unit="g"))
                if olive_oil:
                    db.session.add(MealItem(meal_id=m2.id, food_id=olive_oil.id, quantity=15.0, unit="g"))
                if avocado:
                    db.session.add(MealItem(meal_id=m2.id, food_id=avocado.id, quantity=80.0, unit="g"))

                m3 = Meal(user_id=user.id, meal_date=day, meal_time=time(16, 30), meal_type="Snack")
                db.session.add(m3)
                db.session.flush()
                db.session.add(MealItem(meal_id=m3.id, food_id=yogurt.id, quantity=180.0, unit="g"))
                if almonds:
                    db.session.add(MealItem(meal_id=m3.id, food_id=almonds.id, quantity=35.0, unit="g"))

                m4 = Meal(user_id=user.id, meal_date=day, meal_time=time(20, 0), meal_type="Dinner")
                db.session.add(m4)
                db.session.flush()
                db.session.add(MealItem(meal_id=m4.id, food_id=salmon.id if salmon else chicken.id, quantity=180.0, unit="g"))
                if sweet_potato:
                    db.session.add(MealItem(meal_id=m4.id, food_id=sweet_potato.id, quantity=200.0, unit="g"))
                else:
                    db.session.add(MealItem(meal_id=m4.id, food_id=rice.id, quantity=180.0, unit="g"))

            # Hydration logs throughout the day
            if num_meals > 0:
                water_total = rng.choice([2000.0, 2250.0, 2500.0, 2750.0])
                db.session.add(WaterIntake(user_id=user.id, intake_datetime=datetime.combine(day, time(9, 0)), quantity_ml=500.0))
                db.session.add(WaterIntake(user_id=user.id, intake_datetime=datetime.combine(day, time(13, 30)), quantity_ml=750.0))
                db.session.add(WaterIntake(user_id=user.id, intake_datetime=datetime.combine(day, time(17, 30)), quantity_ml=500.0))
                if water_total > 2000:
                    db.session.add(WaterIntake(user_id=user.id, intake_datetime=datetime.combine(day, time(20, 30)), quantity_ml=water_total - 1750.0))
            else:
                # Minimal intake on rest day
                db.session.add(WaterIntake(user_id=user.id, intake_datetime=datetime.combine(day, time(14, 0)), quantity_ml=750.0))

            # Weight progression log every 3 days
            if offset % 3 == 0 or offset == 0:
                if offset == 0:
                    weight_val = 72.0
                else:
                    weight_val = round(72.0 + (3.2 * (offset / 83.0)) + (0.1 if offset % 2 == 0 else -0.1), 1)
                db.session.add(WeightLog(user_id=user.id, weight_kg=weight_val, measured_on=day))

    # Admin Account
    if not User.query.filter_by(email="admin@nutritrack.com").first():
        admin = User(name="System Administrator", email="admin@nutritrack.com", role="admin", is_active=True)
        admin.set_password("Admin123!")
        db.session.add(admin)
        db.session.flush()
        db.session.add(ActivityLog(user_id=admin.id, action="seed_admin", details="Seeded demo administrator account", ip_address="127.0.0.1"))

    db.session.commit()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    register_error_handlers(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.context_processor
    def inject_globals():
        return {"today": date.today()}

    from .features.auth.routes import auth_bp
    from .features.profile.routes import profile_bp
    from .features.food_catalog.routes import food_catalog_bp
    from .features.meals.routes import meals_bp
    from .features.nutrition.routes import nutrition_bp
    from .features.water.routes import water_bp
    from .features.reminders.routes import reminders_bp
    from .features.dashboard.routes import dashboard_bp
    from .features.admin.routes import admin_bp
    from .features.progress.routes import progress_bp
    from .features.analytics.routes import analytics_bp
    from .features.suggestions.routes import suggestions_bp
    from .features.planner.routes import planner_bp
    from .features.recipes.routes import recipes_bp
    from .features.reports.routes import reports_bp
    from .features.account.routes import account_bp
    from .features.voice.routes import voice_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(food_catalog_bp)
    app.register_blueprint(meals_bp)
    app.register_blueprint(nutrition_bp)
    app.register_blueprint(water_bp)
    app.register_blueprint(reminders_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(suggestions_bp)
    app.register_blueprint(planner_bp)
    app.register_blueprint(recipes_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(voice_bp)

    with app.app_context():
        db.create_all()
        inspector = inspect(db.engine)
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        if "oauth_provider" not in user_columns:
            db.session.execute(text("ALTER TABLE users ADD COLUMN oauth_provider VARCHAR(40)"))
            db.session.commit()
        if "oauth_id" not in user_columns:
            db.session.execute(text("ALTER TABLE users ADD COLUMN oauth_id VARCHAR(120)"))
            db.session.commit()

        profile_columns = {column["name"] for column in inspector.get_columns("profile")}
        if "food_allergies" not in profile_columns:
            db.session.execute(text("ALTER TABLE profile ADD COLUMN food_allergies VARCHAR(500)"))
            db.session.commit()
        
        activity_columns = {column["name"] for column in inspector.get_columns("activity_log")}
        if "ip_address" not in activity_columns:
            db.session.execute(text("ALTER TABLE activity_log ADD COLUMN ip_address VARCHAR(45)"))
            db.session.commit()

        seed_data()
        seed_recipes()
        seed_users()

    return app
