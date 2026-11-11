from datetime import date, timedelta
from collections import defaultdict
from sqlalchemy import func
from app.core.nutrition import item_totals, round_nutrient
from app.extensions import db
from app.models import Goal, Meal, MealItem, WaterIntake


def day_data(user_id, day):
    meals = Meal.query.filter_by(user_id=user_id, meal_date=day).all()
    meal_items = [item for meal in meals for item in meal.items]
    totals = item_totals(meal_items)
    water = db.session.query(func.coalesce(func.sum(WaterIntake.quantity_ml), 0)).filter(
        WaterIntake.user_id == user_id,
        func.date(WaterIntake.intake_datetime) == day,
    ).scalar()
    goal = Goal.query.filter_by(user_id=user_id, status="active").order_by(Goal.start_date.desc()).first()
    totals["water"] = round_nutrient(water)
    return totals, meals, goal


def get_contribution_heatmap(user_id, num_weeks=18):
    """
    Computes a GitHub-inspired contribution matrix for nutrition tracking.
    Returns:
    - weeks: list of columns (each column is 7 days: Sun=0 to Sat=6)
    - month_labels: month headers aligned by week index
    - total_entries: total meals logged in the period
    - total_logged_days: count of days with logged meals
    - streak_days: continuous streak of logged days
    """
    today = date.today()
    # Align to end on upcoming Saturday so the grid layout is square & complete
    sun_weekday = (today.weekday() + 1) % 7
    days_to_saturday = 6 - sun_weekday
    end_date = today + timedelta(days=days_to_saturday)
    start_date = end_date - timedelta(days=(num_weeks * 7) - 1)

    meals = Meal.query.filter(
        Meal.user_id == user_id,
        Meal.meal_date >= start_date,
        Meal.meal_date <= today
    ).all()

    daily_stats = defaultdict(lambda: {"calories": 0.0, "meals_count": 0})
    for m in meals:
        stats = daily_stats[m.meal_date]
        stats["meals_count"] += 1
        for item in m.items:
            basis = 100.0 if item.food.serving_basis == "100g" else 1.0
            stats["calories"] += (item.food.calories * item.quantity) / basis

    goal = Goal.query.filter_by(user_id=user_id, status="active").first()
    target_cals = goal.target_calories if goal else 2000.0

    weeks = []
    month_labels = []
    last_month = None
    total_entries = 0
    total_logged_days = 0

    cur_day = start_date
    for week_idx in range(num_weeks):
        week_days = []
        for day_of_week in range(7):
            d = cur_day
            is_future = d > today
            stats = daily_stats[d] if not is_future else {"calories": 0.0, "meals_count": 0}
            cals = round(stats["calories"])
            m_count = stats["meals_count"]

            if m_count > 0 and not is_future:
                total_logged_days += 1
                total_entries += m_count

            # Determine intensity level (0 to 4 in jade green)
            if is_future or m_count == 0:
                level = 0
            elif cals < target_cals * 0.35:
                level = 1
            elif cals < target_cals * 0.70:
                level = 2
            elif cals < target_cals * 1.15:
                level = 4
            else:
                level = 3

            # Clean tooltip text
            if is_future:
                tooltip = f"{d.strftime('%a, %d %b')}: Upcoming"
            elif m_count == 0:
                tooltip = f"No meals logged on {d.strftime('%a, %d %b')}"
            else:
                status_str = "Target achieved" if level == 4 else f"{cals} kcal"
                tooltip = f"{d.strftime('%a, %d %b')}: {cals} kcal ({m_count} meal{'s' if m_count > 1 else ''}) - {status_str}"

            week_days.append({
                "date": d.isoformat(),
                "label": d.strftime("%d %b"),
                "level": level,
                "calories": cals,
                "meals_count": m_count,
                "tooltip": tooltip,
                "is_today": d == today,
                "is_future": is_future
            })

            # Check month header for Sunday column
            if day_of_week == 0:
                m_name = d.strftime("%b")
                if m_name != last_month:
                    month_labels.append({"name": m_name, "col": week_idx})
                    last_month = m_name

            cur_day += timedelta(days=1)

        weeks.append(week_days)

    # Current streak calculation
    streak_days = 0
    check_day = today
    while True:
        if daily_stats[check_day]["meals_count"] > 0:
            streak_days += 1
            check_day -= timedelta(days=1)
        else:
            break

    return {
        "weeks": weeks,
        "month_labels": month_labels,
        "total_entries": total_entries,
        "total_logged_days": total_logged_days,
        "streak_days": streak_days,
        "num_weeks": num_weeks
    }


def get_daily_reminders_and_insights(user_id, today=None):
    """
    Computes real-time dynamic nutrition reminders and health insights for today:
    - Low protein intake warning detailing catabolism, immune decline, and fatigue
    - Hydration deficit reminder detailing cellular and cognitive impact with quick log
    - Caloric energy balance overview
    - Food recommendations curated for protein recovery
    """
    if today is None:
        today = date.today()
    totals, meals, goal = day_data(user_id, today)

    target_calories = float(goal.target_calories) if goal else 2000.0
    target_protein = float(goal.target_protein) if goal else 120.0
    target_water = float(goal.target_water_ml) if goal else 2500.0

    logged_protein = float(totals.get("protein", 0.0))
    logged_water = float(totals.get("water", 0.0))
    logged_calories = float(totals.get("calories", 0.0))

    # 1. Protein Intake Analysis & Reminder
    protein_deficit = max(target_protein - logged_protein, 0.0)
    protein_ratio = (logged_protein / target_protein) if target_protein > 0 else 1.0
    protein_is_low = protein_ratio < 0.70

    if protein_ratio < 0.35:
        protein_severity = "danger"
        protein_badge = "CRITICAL PROTEIN DEFICIT"
    elif protein_ratio < 0.70:
        protein_severity = "warning"
        protein_badge = "LOW PROTEIN WARNING"
    else:
        protein_severity = "success"
        protein_badge = "PROTEIN TARGET ON TRACK"

    protein_health_warning = (
        "Consuming inadequate dietary protein compromises vital physiological functions. "
        "When intake falls below metabolic requirements, the body enters muscle catabolism—breaking "
        "down lean skeletal muscle tissue to supply essential amino acids for visceral organs. "
        "Inadequate protein additionally impairs immune defense, slows resting metabolic rate, "
        "induces frequent hunger spikes, and leads to persistent fatigue and delayed recovery."
    )

    protein_suggestions = [
        {"name": "Chicken Breast", "protein": "31g / 100g", "calories": "165 kcal", "benefit": "Lean complete animal protein high in branched-chain leucine"},
        {"name": "Greek Yogurt", "protein": "10g / 100g", "calories": "59 kcal", "benefit": "Casein-dense dairy with natural gut-friendly cultures"},
        {"name": "Whole Eggs", "protein": "13g / 100g", "calories": "143 kcal", "benefit": "Complete biological value protein with essential choline"},
        {"name": "Lentils / Dal", "protein": "9g / 100g", "calories": "116 kcal", "benefit": "Plant protein paired with high prebiotic soluble fiber"},
        {"name": "Paneer / Cottage Cheese", "protein": "18g / 100g", "calories": "265 kcal", "benefit": "Slow-release sustained amino acid delivery"},
        {"name": "Firm Tofu", "protein": "8g / 100g", "calories": "76 kcal", "benefit": "Complete plant protein low in saturated fatty acids"},
    ]

    protein_reminder = {
        "title": "Protein Intake & Lean Mass Preservation",
        "badge": protein_badge,
        "severity": protein_severity,
        "is_low": protein_is_low,
        "consumed": round(logged_protein, 1),
        "target": round(target_protein, 1),
        "remaining": round(protein_deficit, 1),
        "percentage": min(round(protein_ratio * 100), 100),
        "warning_text": protein_health_warning,
        "action_text": f"You need {round(protein_deficit, 1)}g more protein today to protect lean muscle tissue and cellular metabolism." if protein_deficit > 0 else "Optimal daily protein target fulfilled.",
        "food_recommendations": protein_suggestions
    }

    # 2. Hydration Balance & Reminder
    water_deficit = max(target_water - logged_water, 0.0)
    water_ratio = (logged_water / target_water) if target_water > 0 else 1.0
    water_is_low = water_ratio < 1.0

    if water_ratio < 0.40:
        water_severity = "warning"
        water_badge = "HYDRATION DEFICIT"
    elif water_ratio < 1.0:
        water_severity = "info"
        water_badge = "HYDRATION IN PROGRESS"
    else:
        water_severity = "success"
        water_badge = "HYDRATION TARGET MET"

    hydration_health_note = (
        "Maintaining cellular hydration is essential for renal waste clearance, blood volume stability, "
        "joint lubrication, cognitive concentration, and efficient nutrient delivery. Even mild 1-2% dehydration "
        "degrades executive cognitive function and increases perception of physical exertion."
    )

    water_reminder = {
        "title": "Hydration Balance & Cellular Vitality",
        "badge": water_badge,
        "severity": water_severity,
        "is_low": water_is_low,
        "consumed_ml": round(logged_water),
        "target_ml": round(target_water),
        "remaining_ml": round(water_deficit),
        "percentage": min(round(water_ratio * 100), 100),
        "health_note": hydration_health_note,
        "action_text": f"Drink {round(water_deficit)} ml more to reach your daily hydration benchmark." if water_deficit > 0 else "Daily hydration target achieved.",
    }

    # 3. Caloric Energy Balance
    cals_remaining = max(target_calories - logged_calories, 0.0)
    calorie_insight = {
        "title": "Daily Caloric Balance",
        "consumed": round(logged_calories),
        "target": round(target_calories),
        "remaining": round(cals_remaining),
        "percentage": min(round((logged_calories / target_calories) * 100), 100) if target_calories > 0 else 0,
        "is_deficit": logged_calories < target_calories,
        "summary": f"{round(cals_remaining)} kcal remaining today toward your {round(target_calories)} kcal daily target." if cals_remaining > 50 else "Daily energetic intake goal achieved."
    }

    # 4. Concise bullet list for quick reading
    bullet_insights = []
    if protein_is_low:
        bullet_insights.append(
            f"Protein intake is currently at {round(logged_protein, 1)}g of {round(target_protein, 1)}g target. "
            f"Low protein can cause muscle catabolism and fatigue; consume protein-rich whole foods like chicken breast, eggs, or Greek yogurt."
        )
    else:
        bullet_insights.append(f"Protein intake is on schedule: {round(logged_protein, 1)}g of {round(target_protein, 1)}g logged.")

    if water_is_low:
        bullet_insights.append(
            f"Hydration reminder: {round(logged_water)} ml of {round(target_water)} ml logged ({round(water_deficit)} ml remaining). "
            f"Maintain fluid balance to support renal filtration and physical energy."
        )
    else:
        bullet_insights.append(f"Hydration benchmark completed: {round(logged_water)} ml logged today.")

    if cals_remaining > 100:
        bullet_insights.append(f"Caloric pace: {round(cals_remaining)} calories remaining today toward your {round(target_calories)} kcal goal.")

    return {
        "protein_reminder": protein_reminder,
        "water_reminder": water_reminder,
        "calorie_insight": calorie_insight,
        "bullet_insights": bullet_insights,
    }
