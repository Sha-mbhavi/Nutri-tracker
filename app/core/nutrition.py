from decimal import Decimal, ROUND_HALF_UP


def round_nutrient(value):
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def item_totals(items):
    result = {key: 0.0 for key in ("calories", "protein", "carbs", "fat", "fiber")}
    for item in items:
        divisor = 100 if item.food.serving_basis == "100g" else 1
        factor = item.quantity / divisor
        for key in result:
            result[key] += getattr(item.food, key) * factor
    return {key: round_nutrient(value) for key, value in result.items()}
