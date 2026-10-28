import pytest
from app import create_app
from app.models import db, User, FoodItem, Meal, MealItem

@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "test"})
    with app.test_client() as client:
        yield client

def register(client, email="user@example.com"):
    return client.post("/register", data={"name":"Test User", "email":email, "password":"secret123", "confirm_password":"secret123"}, follow_redirects=True)

def test_registration_hashes_password(client):
    register(client)
    with client.application.app_context():
        user = User.query.filter_by(email="user@example.com").first()
        assert user.password_hash != "secret123"
        assert user.check_password("secret123")

def test_protected_dashboard_requires_login(client):
    response = client.get("/dashboard", follow_redirects=True)
    assert b"Log in to NutriTrack" in response.data

def test_registration_and_meal_calculation(client):
    register(client)
    client.post("/meals", data={"food_id":"1", "quantity":"50", "meal_type":"Breakfast"}, follow_redirects=True)
    with client.application.app_context():
        user = User.query.filter_by(email="user@example.com").first()
        meal = Meal.query.filter_by(user_id=user.id).first()
        assert len(meal.items) == 1
        item = meal.items[0]
        assert item.food.calories * item.quantity / 100 == 61.5

def test_mismatched_passwords_are_rejected(client):
    response = client.post("/register", data={
        "name": "Test User", "email": "mismatch@example.com",
        "password": "secret123", "confirm_password": "different123"
    }, follow_redirects=True)
    assert b"Passwords do not match" in response.data
    with client.application.app_context():
        assert User.query.filter_by(email="mismatch@example.com").first() is None


def test_duplicate_registration_is_rejected(client):
    register(client)
    client.get("/logout")
    response = register(client)
    assert b"already exists" in response.data

def test_login_redirects_authenticated_user_to_dashboard(client):
    register(client)
    client.get("/logout")
    response = client.post("/login", data={
        "email": "user@example.com", "password": "secret123"
    })
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")


def test_profile_can_store_optional_personal_details(client):
    register(client)
    response = client.post("/profile", data={
        "date_of_birth": "2006-01-15",
        "height_cm": "175",
        "weight_kg": "70",
        "activity_level": "Moderate",
        "diet_preference": "Vegetarian",
        "food_allergies": "Peanuts",
        "nutrition_goal": "Muscle gain"
    }, follow_redirects=True)
    assert response.status_code == 200
    with client.application.app_context():
        user = User.query.filter_by(email="user@example.com").first()
        profile = user.profile
        assert profile.date_of_birth.isoformat() == "2006-01-15"
        assert profile.height_cm == 175
        assert profile.weight_kg == 70
        assert profile.food_allergies == "Peanuts"
        assert profile.nutrition_goal == "Muscle gain"


def test_profile_allows_optional_fields_to_be_skipped(client):
    register(client)
    response = client.post("/profile", data={"height_cm": "", "weight_kg": "", "activity_level": ""}, follow_redirects=True)
    assert b"Profile updated" in response.data


def test_profile_rejects_invalid_measurements(client):
    register(client)
    response = client.post("/profile", data={"height_cm": "500", "weight_kg": "70"}, follow_redirects=True)
    assert b"Enter valid profile values" in response.data


def test_negative_water_is_rejected(client):
    register(client)
    response = client.post("/water", data={"quantity":"-5"}, follow_redirects=True)
    assert b"greater than zero" in response.data
