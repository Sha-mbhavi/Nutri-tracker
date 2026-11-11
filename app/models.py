from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(30), nullable=False, default="user")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    oauth_provider = db.Column(db.String(40), nullable=True)
    oauth_id = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    profile = db.relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    goals = db.relationship("Goal", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date)
    height_cm = db.Column(db.Float)
    weight_kg = db.Column(db.Float)
    activity_level = db.Column(db.String(40))
    diet_preference = db.Column(db.String(40))
    food_allergies = db.Column(db.String(500))
    nutrition_goal = db.Column(db.String(40))
    user = db.relationship("User", back_populates="profile")

class FoodCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    foods = db.relationship("FoodItem", back_populates="category")

class FoodItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("food_category.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False, index=True)
    serving_basis = db.Column(db.String(20), nullable=False, default="100g")
    calories = db.Column(db.Float, nullable=False, default=0)
    protein = db.Column(db.Float, nullable=False, default=0)
    carbs = db.Column(db.Float, nullable=False, default=0)
    fat = db.Column(db.Float, nullable=False, default=0)
    fiber = db.Column(db.Float, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    category = db.relationship("FoodCategory", back_populates="foods")

class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    meal_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    meal_time = db.Column(db.Time)
    meal_type = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    items = db.relationship("MealItem", back_populates="meal", cascade="all, delete-orphan")

class MealItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meal_id = db.Column(db.Integer, db.ForeignKey("meal.id", ondelete="CASCADE"), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey("food_item.id"), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False, default="g")
    meal = db.relationship("Meal", back_populates="items")
    food = db.relationship("FoodItem")

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_calories = db.Column(db.Float, nullable=False)
    target_protein = db.Column(db.Float, nullable=False)
    target_carbs = db.Column(db.Float, nullable=False)
    target_fat = db.Column(db.Float, nullable=False)
    target_fiber = db.Column(db.Float, nullable=False)
    target_water_ml = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(20), nullable=False, default="active")
    user = db.relationship("User", back_populates="goals")

class WaterIntake(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    intake_datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    quantity_ml = db.Column(db.Float, nullable=False)

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reminder_type = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    reminder_time = db.Column(db.Time, nullable=False)
    repeat_rule = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, nullable=False, default=True)

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    action = db.Column(db.String(80), nullable=False)
    details = db.Column(db.String(500))
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class WeightLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    weight_kg = db.Column(db.Float, nullable=False)
    measured_on = db.Column(db.Date, nullable=False, default=date.today, index=True)


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    ingredients = db.Column(db.String(1000), nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    dietary_tags = db.Column(db.String(300))


class PlannedMeal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    planned_date = db.Column(db.Date, nullable=False, index=True)
    meal_type = db.Column(db.String(20), nullable=False)
    foods = db.Column(db.String(500), nullable=False)


class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    meal_reminders_enabled = db.Column(db.Boolean, nullable=False, default=False)
    water_reminders_enabled = db.Column(db.Boolean, nullable=False, default=False)
    reminder_interval_minutes = db.Column(db.Integer, nullable=False, default=120)
