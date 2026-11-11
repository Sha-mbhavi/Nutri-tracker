import pytest
from datetime import date, time
from app.extensions import db
from app.models import Goal, Meal, MealItem, Reminder, User, WaterIntake
from app.features.dashboard.services import get_daily_reminders_and_insights


def register_and_login_user(client, email="health.user@example.com"):
    client.post("/register", data={
        "name": "Health User",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    }, follow_redirects=True)
    client.post("/login", data={
        "email": email,
        "password": "Password123!"
    }, follow_redirects=True)


def test_daily_insights_identifies_low_protein_and_hydration_deficit(client):
    """
    Verifies that low protein intake is flagged with explicit clinical health warnings,
    and hydration deficit is accurately calculated with actionable targets.
    """
    register_and_login_user(client)

    with client.application.app_context():
        user = User.query.filter_by(email="health.user@example.com").first()
        assert user is not None

        # Set goal: 120g protein, 2500ml water
        goal = Goal.query.filter_by(user_id=user.id, status="active").first()
        if not goal:
            goal = Goal(
                user_id=user.id,
                target_calories=2000.0,
                target_protein=120.0,
                target_carbs=220.0,
                target_fat=65.0,
                target_fiber=30.0,
                target_water_ml=2500.0,
                status="active"
            )
            db.session.add(goal)
            db.session.commit()

        # Compute insights with 0 logged intake
        insights = get_daily_reminders_and_insights(user.id, date.today())
        p_rem = insights["protein_reminder"]
        w_rem = insights["water_reminder"]

        # Low protein checks
        assert p_rem["is_low"] is True
        assert p_rem["consumed"] == 0.0
        assert p_rem["target"] == 120.0
        assert p_rem["remaining"] == 120.0
        assert "catabolism" in p_rem["warning_text"].lower()
        assert "immune" in p_rem["warning_text"].lower()
        assert len(p_rem["food_recommendations"]) > 0

        # Hydration deficit checks
        assert w_rem["is_low"] is True
        assert w_rem["consumed_ml"] == 0
        assert w_rem["target_ml"] == 2500
        assert w_rem["remaining_ml"] == 2500
        assert "renal" in w_rem["health_note"].lower()


def test_quick_water_logging_with_next_redirect(client):
    """
    Verifies that logging water with a `next` parameter logs the intake
    and redirects safely back to the originating page.
    """
    register_and_login_user(client)

    # Quick log 500 ml from dashboard
    res = client.post("/water", data={
        "quantity": "500",
        "next": "/dashboard"
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"Water intake saved." in res.data
    assert b"500" in res.data

    with client.application.app_context():
        user = User.query.filter_by(email="health.user@example.com").first()
        water_entry = WaterIntake.query.filter_by(user_id=user.id).order_by(WaterIntake.id.desc()).first()
        assert water_entry is not None
        assert water_entry.quantity_ml == 500.0


def test_reminders_page_renders_active_insights_and_supports_crud(client):
    """
    Verifies that the /reminders page displays:
    1. Active physiological health alerts (low protein warning & water reminder)
    2. Scheduled reminder creation, toggling on/off, and deletion.
    """
    register_and_login_user(client)

    # 1. GET /reminders displays active insights
    res_get = client.get("/reminders")
    assert res_get.status_code == 200
    assert b"Clinical Alert" in res_get.data or b"Low Dietary Protein" in res_get.data
    assert b"Hydration Reminder" in res_get.data or b"Hydration Notice" in res_get.data

    # 2. POST /reminders creates a scheduled prompt
    res_post = client.post("/reminders", data={
        "title": "Evening Protein Shake",
        "reminder_type": "Meal",
        "reminder_time": "18:30",
        "repeat_rule": "Daily"
    }, follow_redirects=True)

    assert res_post.status_code == 200
    assert b"Reminder created." in res_post.data
    assert b"Evening Protein Shake" in res_post.data

    with client.application.app_context():
        user = User.query.filter_by(email="health.user@example.com").first()
        rem = Reminder.query.filter_by(user_id=user.id, title="Evening Protein Shake").first()
        assert rem is not None
        assert rem.is_active is True
        rem_id = rem.id

    # 3. Toggle reminder status
    res_toggle = client.post(f"/reminders/{rem_id}/toggle", follow_redirects=True)
    assert res_toggle.status_code == 200
    assert b"Reminder updated." in res_toggle.data

    with client.application.app_context():
        rem = db.session.get(Reminder, rem_id)
        assert rem.is_active is False

    # 4. Delete reminder
    res_delete = client.post(f"/reminders/{rem_id}/delete", follow_redirects=True)
    assert res_delete.status_code == 200
    assert b"Reminder deleted." in res_delete.data

    with client.application.app_context():
        assert db.session.get(Reminder, rem_id) is None


def test_dashboard_renders_protein_warning_and_water_reminders(client):
    """
    Verifies that /dashboard contains the active protein warning and hydration quick-log controls.
    """
    register_and_login_user(client)

    res = client.get("/dashboard")
    assert res.status_code == 200
    assert b"Active Health Insights" in res.data
    assert b"Inadequate Dietary Protein" in res.data
    assert b"Quick Log Water Intake" in res.data
    assert b"+250 ml (Glass)" in res.data
