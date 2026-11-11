-- ============================================================================
-- NutriTrack Relational Database Management System (RDBMS) Schema Script
-- Course: Integrated Full-Stack Project (RDBMS Component)
-- Architecture: Third Normal Form (3NF) Relational Design
-- Compatible with: SQLite 3.x / Azure Database for PostgreSQL / Azure SQL
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1. USERS TABLE (Primary Authentication & Role Entity)
-- Normal Form: 3NF - All non-key attributes dependent strictly on PK id
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(180) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin', 'mentor')),
    is_active BOOLEAN NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2. PROFILE TABLE (1:1 Extension for Personal & Biometric Metrics)
-- Normal Form: 3NF - De-coupled from auth credentials to eliminate nulls & transitive dependencies
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    date_of_birth DATE,
    height_cm REAL CHECK (height_cm IS NULL OR (height_cm > 40 AND height_cm < 280)),
    weight_kg REAL CHECK (weight_kg IS NULL OR (weight_kg > 20 AND weight_kg < 350)),
    activity_level VARCHAR(40),
    diet_preference VARCHAR(40),
    food_allergies VARCHAR(500),
    nutrition_goal VARCHAR(40),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 3. FOOD_CATEGORY TABLE (Lookup Dimension Table for Nutrition Catalog)
-- Normal Form: 3NF - Prevents repeating string literals and insertion anomalies
-- Standardized 7 Core Categories:
--   1. 'Whole Grains & Staples'   (e.g., Brown Rice, Oats, Quinoa, Chapati)
--   2. 'Lean Proteins'           (e.g., Chicken Breast, Salmon, Egg Whites)
--   3. 'Vegetables & Greens'     (e.g., Broccoli, Spinach, Kale, Bell Pepper)
--   4. 'Fruits & Berries'        (e.g., Banana, Blueberries, Apple, Strawberries)
--   5. 'Plant Proteins & Legumes'(e.g., Dal, Chickpeas, Tofu, Black Beans)
--   6. 'Dairy & Cultured'        (e.g., Greek Yogurt, Paneer, Cottage Cheese)
--   7. 'Nuts, Seeds & Healthy Fats' (e.g., Almonds, Chia Seeds, Avocado)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS food_category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(80) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);

-- ----------------------------------------------------------------------------
-- 4. FOOD_ITEM TABLE (Nutrient Master Table)
-- Normal Form: 3NF - Normalized by category_id, nutrient quantities per 100g basis
-- Master whole foods catalog: 50+ diverse items with validated calories, protein,
-- carbohydrates, fat, and dietary fiber per 100g serving basis.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS food_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    name VARCHAR(120) NOT NULL,
    serving_basis VARCHAR(20) NOT NULL DEFAULT '100g',
    calories REAL NOT NULL DEFAULT 0 CHECK (calories >= 0),
    protein REAL NOT NULL DEFAULT 0 CHECK (protein >= 0),
    carbs REAL NOT NULL DEFAULT 0 CHECK (carbs >= 0),
    fat REAL NOT NULL DEFAULT 0 CHECK (fat >= 0),
    fiber REAL NOT NULL DEFAULT 0 CHECK (fiber >= 0),
    is_active BOOLEAN NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    FOREIGN KEY (category_id) REFERENCES food_category (id) ON DELETE RESTRICT
);

-- ----------------------------------------------------------------------------
-- 5. MEAL TABLE (Header Table for Meal Occurrences)
-- Normal Form: 3NF - Captures user event context (date, time, category)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS meal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    meal_date DATE NOT NULL,
    meal_time TIME,
    meal_type VARCHAR(20) NOT NULL CHECK (meal_type IN ('Breakfast', 'Lunch', 'Dinner', 'Snack')),
    notes VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 6. MEAL_ITEM TABLE (Associative Entity: Resolves M:N Between Meal & FoodItem)
-- Normal Form: 3NF - Quantity-based consumption record without transitive nutritional data
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS meal_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meal_id INTEGER NOT NULL,
    food_id INTEGER NOT NULL,
    quantity REAL NOT NULL CHECK (quantity > 0),
    unit VARCHAR(20) NOT NULL DEFAULT 'g',
    FOREIGN KEY (meal_id) REFERENCES meal (id) ON DELETE CASCADE,
    FOREIGN KEY (food_id) REFERENCES food_item (id) ON DELETE RESTRICT
);

-- ----------------------------------------------------------------------------
-- 7. GOAL TABLE (User Daily Nutritional & Hydration Targets)
-- Normal Form: 3NF - Historical or active targets per user
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS goal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    target_calories REAL NOT NULL CHECK (target_calories >= 0),
    target_protein REAL NOT NULL CHECK (target_protein >= 0),
    target_carbs REAL NOT NULL CHECK (target_carbs >= 0),
    target_fat REAL NOT NULL CHECK (target_fat >= 0),
    target_fiber REAL NOT NULL CHECK (target_fiber >= 0),
    target_water_ml REAL NOT NULL CHECK (target_water_ml >= 0),
    start_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived', 'paused')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 8. WATER_INTAKE TABLE (Hydration Log Stream)
-- Normal Form: 3NF - Timestamped individual fluid intake entries
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS water_intake (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    intake_datetime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    quantity_ml REAL NOT NULL CHECK (quantity_ml > 0),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 9. WEIGHT_LOG TABLE (User Biometric Progress Tracking)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS weight_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    weight_kg REAL NOT NULL CHECK (weight_kg > 20 AND weight_kg < 350),
    measured_on DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 10. ACTIVITY_LOG TABLE (Security Audit Trail & Compliance)
-- Cloud Security Requirement: Tamper-evident user activity log with IP tracking
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action VARCHAR(80) NOT NULL,
    details VARCHAR(500),
    ip_address VARCHAR(45),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
);

-- ----------------------------------------------------------------------------
-- 11. REMINDER TABLE (Notification Schedule)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reminder (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    reminder_type VARCHAR(20) NOT NULL,
    title VARCHAR(120) NOT NULL,
    reminder_time TIME NOT NULL,
    repeat_rule VARCHAR(120),
    is_active BOOLEAN NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 12. RECIPES & PLANNED MEALS (Semi-Structured Relational Schemas)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS recipe (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(120) NOT NULL,
    ingredients TEXT NOT NULL,
    instructions TEXT NOT NULL,
    dietary_tags VARCHAR(300)
);

CREATE TABLE IF NOT EXISTS planned_meal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    planned_date DATE NOT NULL,
    meal_type VARCHAR(20) NOT NULL,
    foods VARCHAR(500) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- ============================================================================
-- INDEXES (Optimized for frequent search, join, and filter queries)
-- ============================================================================
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_food_item_name ON food_item(name);
CREATE INDEX IF NOT EXISTS ix_food_item_category ON food_item(category_id);
CREATE INDEX IF NOT EXISTS ix_meal_user_date ON meal(user_id, meal_date);
CREATE INDEX IF NOT EXISTS ix_meal_item_meal ON meal_item(meal_id);
CREATE INDEX IF NOT EXISTS ix_water_intake_user_time ON water_intake(user_id, intake_datetime);
CREATE INDEX IF NOT EXISTS ix_activity_log_user_created ON activity_log(user_id, created_at);

-- ============================================================================
-- VIEWS (RDBMS Requirement: Computed Analytical & Summary Views)
-- ============================================================================

-- View 1: Daily Aggregated Nutrition Summary per User
CREATE VIEW IF NOT EXISTS daily_nutrition_summary AS
SELECT 
    m.user_id, 
    m.meal_date,
    COUNT(DISTINCT m.id) AS total_meals_logged,
    COUNT(mi.id) AS total_food_items,
    ROUND(SUM(fi.calories * mi.quantity / CASE WHEN fi.serving_basis = '100g' THEN 100.0 ELSE 1.0 END), 2) AS calories,
    ROUND(SUM(fi.protein * mi.quantity / CASE WHEN fi.serving_basis = '100g' THEN 100.0 ELSE 1.0 END), 2) AS protein,
    ROUND(SUM(fi.carbs * mi.quantity / CASE WHEN fi.serving_basis = '100g' THEN 100.0 ELSE 1.0 END), 2) AS carbs,
    ROUND(SUM(fi.fat * mi.quantity / CASE WHEN fi.serving_basis = '100g' THEN 100.0 ELSE 1.0 END), 2) AS fat,
    ROUND(SUM(fi.fiber * mi.quantity / CASE WHEN fi.serving_basis = '100g' THEN 100.0 ELSE 1.0 END), 2) AS fiber
FROM meal m 
JOIN meal_item mi ON mi.meal_id = m.id 
JOIN food_item fi ON fi.id = mi.food_id
GROUP BY m.user_id, m.meal_date;

-- View 2: Goal vs. Actual Compliance Analytical View
CREATE VIEW IF NOT EXISTS user_goal_compliance_view AS
SELECT 
    dns.user_id,
    dns.meal_date,
    dns.calories AS actual_calories,
    g.target_calories,
    ROUND(dns.calories - g.target_calories, 2) AS calorie_variance,
    dns.protein AS actual_protein,
    g.target_protein,
    dns.carbs AS actual_carbs,
    g.target_carbs,
    dns.fat AS actual_fat,
    g.target_fat
FROM daily_nutrition_summary dns
JOIN goal g ON g.user_id = dns.user_id AND g.status = 'active';

-- ============================================================================
-- TRIGGERS (RDBMS Requirement: Automated Business Logic & Audit Trail)
-- Automatically inserts an entry into activity_log whenever a meal_item is added
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS trg_audit_meal_item_insert
AFTER INSERT ON meal_item
FOR EACH ROW
BEGIN
    INSERT INTO activity_log (user_id, action, details, ip_address, created_at)
    SELECT 
        m.user_id,
        'meal_item_logged_trigger',
        'Automatic audit trigger: Added food_id ' || NEW.food_id || ' (' || NEW.quantity || 'g) to meal_id ' || NEW.meal_id,
        '127.0.0.1',
        CURRENT_TIMESTAMP
    FROM meal m
    WHERE m.id = NEW.meal_id;
END;

-- ============================================================================
-- REFERENCE SEED DEFINITIONS (Aligned with app/__init__.py)
-- Standard 7 Categories and Representative 50+ Whole Food Items
-- ============================================================================
-- Category Reference:
-- INSERT OR IGNORE INTO food_category (id, name) VALUES
--   (1, 'Whole Grains & Staples'),
--   (2, 'Lean Proteins'),
--   (3, 'Vegetables & Greens'),
--   (4, 'Fruits & Berries'),
--   (5, 'Plant Proteins & Legumes'),
--   (6, 'Dairy & Cultured'),
--   (7, 'Nuts, Seeds & Healthy Fats');
--
-- Food Items Reference (per 100g serving basis):
-- Whole Grains & Staples:
--   Brown Rice (123 kcal, P: 2.7g, C: 25.6g, F: 1.0g, Fiber: 1.6g)
--   Rolled Oats (389 kcal, P: 16.9g, C: 66.3g, F: 6.9g, Fiber: 10.6g)
--   Quinoa (120 kcal, P: 4.4g, C: 21.3g, F: 1.9g, Fiber: 2.8g)
--   Chapati (120 kcal, P: 3.4g, C: 24.0g, F: 1.1g, Fiber: 2.3g)
-- Lean Proteins:
--   Chicken Breast (165 kcal, P: 31.0g, C: 0.0g, F: 3.6g, Fiber: 0.0g)
--   Salmon Fillet (208 kcal, P: 20.4g, C: 0.0g, F: 13.4g, Fiber: 0.0g)
--   Whole Egg (143 kcal, P: 12.6g, C: 0.7g, F: 9.5g, Fiber: 0.0g)
-- Vegetables & Greens:
--   Broccoli (34 kcal, P: 2.8g, C: 6.6g, F: 0.4g, Fiber: 2.6g)
--   Baby Spinach (23 kcal, P: 2.9g, C: 3.6g, F: 0.4g, Fiber: 2.2g)
-- Fruits & Berries:
--   Banana (89 kcal, P: 1.1g, C: 22.8g, F: 0.3g, Fiber: 2.6g)
--   Blueberries (57 kcal, P: 0.7g, C: 14.5g, F: 0.3g, Fiber: 2.4g)
-- Plant Proteins & Legumes:
--   Dal (116 kcal, P: 9.0g, C: 20.0g, F: 0.8g, Fiber: 7.9g)
--   Chickpeas (164 kcal, P: 8.9g, C: 27.4g, F: 2.6g, Fiber: 7.6g)
-- Dairy & Cultured:
--   Greek Yogurt (59 kcal, P: 10.0g, C: 3.6g, F: 0.4g, Fiber: 0.0g)
--   Paneer (265 kcal, P: 18.0g, C: 1.2g, F: 20.0g, Fiber: 0.0g)
-- Nuts, Seeds & Healthy Fats:
--   Raw Almonds (579 kcal, P: 21.2g, C: 21.6g, F: 49.9g, Fiber: 12.5g)
--   Extra Virgin Olive Oil (884 kcal, P: 0.0g, C: 0.0g, F: 100.0g, Fiber: 0.0g)
--   Avocado (160 kcal, P: 2.0g, C: 8.5g, F: 14.7g, Fiber: 6.7g)
-- ============================================================================
