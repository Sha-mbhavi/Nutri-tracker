import os
from datetime import date
from flask import Flask
from sqlalchemy import inspect, text

from config import Config
from .extensions import db, login_manager
from .models import FoodCategory, FoodItem, Recipe, User
from .core.errors import register_error_handlers


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
        profile_columns = {column["name"] for column in inspect(db.engine).get_columns("profile")}
        if "food_allergies" not in profile_columns:
            db.session.execute(text("ALTER TABLE profile ADD COLUMN food_allergies VARCHAR(500)"))
            db.session.commit()
        seed_data()
        seed_recipes()

    return app


def seed_data():
    if FoodItem.query.first():
        return
    category = FoodCategory(name="Staples")
    db.session.add(category)
    db.session.flush()
    foods = [
        ("Brown Rice", "100g", 123, 2.7, 25.6, 1.0, 1.6),
        ("Chicken Breast", "100g", 165, 31, 0, 3.6, 0),
        ("Banana", "100g", 89, 1.1, 22.8, 0.3, 2.6),
        ("Broccoli", "100g", 34, 2.8, 6.6, 0.4, 2.6),
        ("Greek Yogurt", "100g", 59, 10, 3.6, 0.4, 0),
        ("Chapati", "100g", 120, 3.4, 24, 1.1, 2.3),
        ("Dal", "100g", 116, 9, 20, 0.8, 7.9),
        ("Paneer", "100g", 265, 18, 1.2, 20, 0),
        ("Chickpeas", "100g", 164, 8.9, 27.4, 2.6, 7.6),
    ]
    for name, basis, calories, protein, carbs, fat, fiber in foods:
        db.session.add(FoodItem(category_id=category.id, name=name, serving_basis=basis,
            calories=calories, protein=protein, carbs=carbs, fat=fat, fiber=fiber))
    db.session.commit()


def seed_recipes():
    if Recipe.query.first():
        return
    db.session.add_all([
        Recipe(name="Dal and rice", ingredients="dal, rice, onion, tomato", instructions="Cook dal, prepare rice, and serve together.", dietary_tags="Vegetarian"),
        Recipe(name="Paneer tomato stir-fry", ingredients="paneer, tomato, onion", instructions="Saute vegetables, add paneer, and cook until hot.", dietary_tags="Vegetarian"),
        Recipe(name="Vegetable chickpea bowl", ingredients="chickpeas, tomato, broccoli, onion", instructions="Warm chickpeas and vegetables, then season and serve.", dietary_tags="Vegan"),
    ])
    db.session.commit()
