import pytest
from datetime import date, timedelta
from app import create_app
from app.models import db, User, FoodCategory, FoodItem, Meal, WaterIntake, WeightLog
from app.features.dashboard.services import get_contribution_heatmap


@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "test-key-db"})
    with app.test_client() as client:
        yield client


def test_seven_food_categories_and_fifty_plus_foods(client):
    """
    RDBMS Database & Catalog Requirement:
    Verify that 7 distinct food categories and 50+ diverse whole foods are seeded with accurate macros.
    """
    with client.application.app_context():
        categories = FoodCategory.query.filter_by(is_active=True).all()
        cat_names = {c.name for c in categories}
        expected_cats = {
            "Whole Grains & Staples",
            "Lean Proteins",
            "Vegetables & Greens",
            "Fruits & Berries",
            "Plant Proteins & Legumes",
            "Dairy & Cultured",
            "Nuts, Seeds & Healthy Fats",
        }
        assert expected_cats.issubset(cat_names), f"Missing categories: {expected_cats - cat_names}"
        assert len(cat_names) >= 7

        food_count = FoodItem.query.filter_by(is_active=True).count()
        assert food_count >= 50, f"Expected 50+ foods, found {food_count}"

        # Verify Brown Rice is present with 123 calories
        rice = FoodItem.query.filter_by(name="Brown Rice").first()
        assert rice is not None
        assert rice.calories == 123.0
        assert rice.category.name == "Whole Grains & Staples"

        # Verify each category has multiple items
        for cat in categories:
            items = FoodItem.query.filter_by(category_id=cat.id).all()
            assert len(items) >= 5, f"Category {cat.name} has fewer than 5 items: {len(items)}"


def test_historical_user_activity_and_heatmap_intensity(client):
    """
    Heatmap & Analytics Requirement:
    Verify 84 days (12 weeks) of meal logs, water logs, and weight entries for user@nutritrack.com,
    and verify realistic intensity variation covering all 5 levels (0, 1, 2, 3, 4).
    """
    with client.application.app_context():
        user = User.query.filter_by(email="user@nutritrack.com").first()
        assert user is not None

        # Verify historical meals
        meals = Meal.query.filter_by(user_id=user.id).all()
        assert len(meals) >= 50, f"Expected robust historical meal count, found {len(meals)}"

        # Verify heatmap calculation and levels
        heatmap = get_contribution_heatmap(user.id)
        assert heatmap["total_entries"] == len(meals)
        assert heatmap["streak_days"] >= 5, f"Expected streak >= 5, got {heatmap['streak_days']}"

        levels = {d["level"] for w in heatmap["weeks"] for d in w if not d["is_future"]}
        # Verify all levels 0 to 4 are represented
        for expected_lvl in (0, 1, 2, 3, 4):
            assert expected_lvl in levels, f"Heatmap missing expected intensity level {expected_lvl}"

        # Verify water logs
        water_count = WaterIntake.query.filter_by(user_id=user.id).count()
        assert water_count >= 80, f"Expected 80+ water intake logs, found {water_count}"

        # Verify weight logs across the 12 weeks
        weights = WeightLog.query.filter_by(user_id=user.id).order_by(WeightLog.measured_on.asc()).all()
        assert len(weights) >= 20, f"Expected 20+ weight progression entries, found {len(weights)}"
        assert weights[-1].weight_kg == 72.0


def test_food_catalog_category_filtering_and_search(client):
    """
    UI Catalog Navigation Requirement:
    Verify browsing foods by category tab ('all', plus category names) and search text.
    """
    # Log in as demo user
    client.post("/login", data={"email": "user@nutritrack.com", "password": "User123!"}, follow_redirects=True)

    # 1. Access all foods
    res_all = client.get("/foods")
    assert res_all.status_code == 200
    assert b"FOOD CATALOG" in res_all.data
    assert b"Whole Grains &amp; Staples" in res_all.data or b"Whole Grains & Staples" in res_all.data
    assert b"Lean Proteins" in res_all.data
    assert b"Brown Rice" in res_all.data
    assert b"Chicken Breast" in res_all.data

    # 2. Filter by category: Lean Proteins
    res_protein = client.get("/foods?category=Lean+Proteins")
    assert res_protein.status_code == 200
    assert b"Chicken Breast" in res_protein.data
    assert b"Salmon Fillet" in res_protein.data
    assert b"Brown Rice" not in res_protein.data

    # 3. Filter by category: Fruits & Berries
    res_fruits = client.get("/foods?category=Fruits+%26+Berries")
    assert res_fruits.status_code == 200
    assert b"Banana" in res_fruits.data
    assert b"Blueberries" in res_fruits.data
    assert b"Chicken Breast" not in res_fruits.data

    # 4. Search query
    res_search = client.get("/foods?q=salmon")
    assert res_search.status_code == 200
    assert b"Salmon Fillet" in res_search.data
    assert b"Banana" not in res_search.data

    # 5. Combined category and search query
    res_combined = client.get("/foods?category=Lean+Proteins&q=turkey")
    assert res_combined.status_code == 200
    assert b"Turkey Breast" in res_combined.data
    assert b"Chicken Breast" not in res_combined.data
