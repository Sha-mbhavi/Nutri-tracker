from datetime import date


def parse_profile_form(form):
    height = float(form.get("height_cm") or 0) or None
    weight = float(form.get("weight_kg") or 0) or None
    if height is not None and not 1 <= height <= 300:
        raise ValueError
    if weight is not None and not 1 <= weight <= 500:
        raise ValueError
    dob_text = form.get("date_of_birth", "").strip()
    dob = date.fromisoformat(dob_text) if dob_text else None
    if dob and (dob > date.today() or dob.year < 1900):
        raise ValueError
    activity = form.get("activity_level", "").strip()
    goal = form.get("nutrition_goal", "").strip()
    if activity and activity not in {"Low", "Moderate", "High"}:
        raise ValueError
    if goal and goal not in {"Maintain", "Lose weight", "Muscle gain", "Gain strength"}:
        raise ValueError
    return {
        "date_of_birth": dob,
        "height_cm": height,
        "weight_kg": weight,
        "activity_level": activity or None,
        "diet_preference": form.get("diet_preference", "").strip() or None,
        "food_allergies": form.get("food_allergies", "").strip() or None,
        "nutrition_goal": goal or None,
    }
