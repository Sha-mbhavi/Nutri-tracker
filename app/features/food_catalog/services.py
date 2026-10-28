from app.models import FoodItem


def search_active_foods(query=""):
    foods_query = FoodItem.query.filter_by(is_active=True)
    if query:
        foods_query = foods_query.filter(FoodItem.name.ilike(f"%{query}%"))
    return foods_query.all()
