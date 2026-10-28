-- NutriTrack SQLite reference schema
-- Flask-SQLAlchemy creates this schema automatically. These statements document key RDBMS features.
PRAGMA foreign_keys = ON;

CREATE VIEW IF NOT EXISTS daily_nutrition_summary AS
SELECT m.user_id, m.meal_date,
       ROUND(SUM(fi.calories * mi.quantity / CASE WHEN fi.serving_basis = '100g' THEN 100 ELSE 1 END), 2) AS calories,
       ROUND(SUM(fi.protein * mi.quantity / CASE WHEN fi.serving_basis = '100g' THEN 100 ELSE 1 END), 2) AS protein,
       ROUND(SUM(fi.carbs * mi.quantity / CASE WHEN fi.serving_basis = '100g' THEN 100 ELSE 1 END), 2) AS carbs,
       ROUND(SUM(fi.fat * mi.quantity / CASE WHEN fi.serving_basis = '100g' THEN 100 ELSE 1 END), 2) AS fat,
       ROUND(SUM(fi.fiber * mi.quantity / CASE WHEN fi.serving_basis = '100g' THEN 100 ELSE 1 END), 2) AS fiber
FROM meal m JOIN meal_item mi ON mi.meal_id = m.id JOIN food_item fi ON fi.id = mi.food_id
GROUP BY m.user_id, m.meal_date;

-- Related-data JOIN example
SELECT m.meal_type, fi.name, mi.quantity, fi.serving_basis
FROM meal m JOIN meal_item mi ON mi.meal_id = m.id JOIN food_item fi ON fi.id = mi.food_id
WHERE m.user_id = 1 AND m.meal_date = date('now');

CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_food_item_name ON food_item(name);
CREATE INDEX IF NOT EXISTS ix_meal_user_date ON meal(user_id, meal_date);
