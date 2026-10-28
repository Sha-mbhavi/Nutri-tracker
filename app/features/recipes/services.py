def recipe_matches(recipe, ingredients):
    if not ingredients:
        return True
    available = [item.strip().lower() for item in ingredients.split(",") if item.strip()]
    return any(item in (recipe.ingredients or "").lower() for item in available)
