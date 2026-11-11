-- ============================================================================
-- NutriTrack SQL Query Demonstration File
-- Course: Integrated Full-Stack Project (RDBMS Component)
-- Purpose: Demonstrates Multi-Table JOINs, Transactions, Views, Triggers,
--          Stored Procedures, and Index-Optimized Queries
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. MULTI-TABLE JOIN: Comprehensive 5-Table Meal Log with Nutrition
-- Demonstrates: INNER JOIN across users, meal, meal_item, food_item, and food_category
-- ----------------------------------------------------------------------------
SELECT 
    u.name AS user_name,
    u.email AS user_email,
    m.meal_date,
    m.meal_type,
    fc.name AS category,
    fi.name AS food_name,
    mi.quantity AS quantity_grams,
    ROUND(fi.calories * mi.quantity / 100.0, 2) AS calculated_calories,
    ROUND(fi.protein * mi.quantity / 100.0, 2) AS calculated_protein_g,
    ROUND(fi.carbs * mi.quantity / 100.0, 2) AS calculated_carbs_g,
    ROUND(fi.fat * mi.quantity / 100.0, 2) AS calculated_fat_g
FROM users u
JOIN meal m ON m.user_id = u.id
JOIN meal_item mi ON mi.meal_id = m.id
JOIN food_item fi ON fi.id = mi.food_id
JOIN food_category fc ON fc.id = fi.category_id
WHERE u.email = 'user@nutritrack.com'
  AND m.meal_date = CURRENT_DATE
ORDER BY m.meal_type, fi.name;


-- ----------------------------------------------------------------------------
-- 2. LEFT JOIN: Food Items and Consumption Frequency (Identifies Unused Foods)
-- Demonstrates: LEFT OUTER JOIN and aggregate count
-- ----------------------------------------------------------------------------
SELECT 
    fi.id AS food_id,
    fi.name AS food_name,
    fc.name AS category_name,
    fi.calories AS calories_per_100g,
    COUNT(mi.id) AS times_consumed
FROM food_item fi
JOIN food_category fc ON fc.id = fi.category_id
LEFT JOIN meal_item mi ON mi.food_id = fi.id
GROUP BY fi.id, fi.name, fc.name, fi.calories
ORDER BY times_consumed DESC, fi.name ASC;


-- ----------------------------------------------------------------------------
-- 3. EXPLICIT DATABASE TRANSACTION: Atomic Meal Creation with Items
-- Demonstrates: ACID compliance, transactional atomicity, savepoints/rollback
-- ----------------------------------------------------------------------------
BEGIN TRANSACTION;

-- Ensure parent user, category, and food records exist for FK consistency
INSERT OR IGNORE INTO users (id, name, email, password_hash, role)
VALUES (1, 'Sample User', 'user@nutritrack.com', 'pbkdf2:sha256:dummyhash', 'user');

INSERT OR IGNORE INTO food_category (id, name) VALUES (1, 'Whole Grains & Staples');
INSERT OR IGNORE INTO food_category (id, name) VALUES (2, 'Lean Proteins');

INSERT OR IGNORE INTO food_item (id, category_id, name, serving_basis, calories, protein, carbs, fat, fiber)
VALUES (1, 1, 'Brown Rice', '100g', 123, 2.7, 25.6, 1.0, 1.6);

INSERT OR IGNORE INTO food_item (id, category_id, name, serving_basis, calories, protein, carbs, fat, fiber)
VALUES (2, 2, 'Chicken Breast', '100g', 165, 31.0, 0.0, 3.6, 0.0);

-- Step A: Insert the meal header record
INSERT INTO meal (user_id, meal_date, meal_time, meal_type, notes)
VALUES (1, CURRENT_DATE, '13:00:00', 'Lunch', 'Balanced post-workout meal');

-- Step B: Insert associated food items using the generated meal ID
INSERT INTO meal_item (meal_id, food_id, quantity, unit)
VALUES (last_insert_rowid(), 2, 150.0, 'g'); -- 150g Chicken Breast

INSERT INTO meal_item (meal_id, food_id, quantity, unit)
VALUES (last_insert_rowid(), 1, 100.0, 'g'); -- 100g Brown Rice

-- Step C: Log the transactional event into the audit trail
INSERT INTO activity_log (user_id, action, details, ip_address, created_at)
VALUES (1, 'meal_transaction_completed', 'Atomic meal logging transaction executed', '127.0.0.1', CURRENT_TIMESTAMP);

-- Commit transaction atomically
COMMIT;


-- ----------------------------------------------------------------------------
-- 4. QUERYING THE DATABASE VIEW: Daily Aggregated Nutrition Summary
-- Demonstrates: Querying abstract view with filtering and order
-- ----------------------------------------------------------------------------
SELECT 
    user_id,
    meal_date,
    total_meals_logged,
    total_food_items,
    calories,
    protein,
    carbs,
    fat,
    fiber
FROM daily_nutrition_summary
WHERE user_id = 1
  AND meal_date >= DATE('now', '-7 days')
ORDER BY meal_date DESC;


-- ----------------------------------------------------------------------------
-- 5. QUERYING THE COMPLIANCE VIEW: Target vs. Actual Variance
-- Demonstrates: Comparative analytics over active goals and view joins
-- ----------------------------------------------------------------------------
SELECT 
    user_id,
    meal_date,
    actual_calories,
    target_calories,
    calorie_variance,
    CASE 
        WHEN ABS(calorie_variance) <= 150 THEN 'Within Target (±150 kcal)'
        WHEN calorie_variance > 150 THEN 'Exceeded Target'
        ELSE 'Deficit'
    END AS compliance_status,
    actual_protein,
    target_protein
FROM user_goal_compliance_view
WHERE user_id = 1;


-- ----------------------------------------------------------------------------
-- 6. VERIFYING TRIGGER EXECUTION
-- Demonstrates: Checking audit trail populated automatically by trg_audit_meal_item_insert
-- ----------------------------------------------------------------------------
SELECT id, user_id, action, details, ip_address, created_at
FROM activity_log
WHERE action = 'meal_item_logged_trigger'
ORDER BY created_at DESC
LIMIT 5;


-- ----------------------------------------------------------------------------
-- 7. STORED PROCEDURE / FUNCTION DEFINITION (PostgreSQL / Azure SQL Syntax)
-- Demonstrates: RDBMS Stored Procedure requirement for calculating daily macros
-- ----------------------------------------------------------------------------
/*
CREATE OR REPLACE FUNCTION sp_calculate_daily_macros(
    p_user_id INT,
    p_date DATE
)
RETURNS TABLE (
    user_id INT,
    report_date DATE,
    total_calories NUMERIC,
    total_protein NUMERIC,
    total_carbs NUMERIC,
    total_fat NUMERIC,
    water_intake_ml NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH nutrition AS (
        SELECT 
            m.user_id,
            m.meal_date,
            ROUND(SUM(fi.calories * mi.quantity / 100.0), 2) AS cals,
            ROUND(SUM(fi.protein * mi.quantity / 100.0), 2) AS prot,
            ROUND(SUM(fi.carbs * mi.quantity / 100.0), 2) AS crb,
            ROUND(SUM(fi.fat * mi.quantity / 100.0), 2) AS ft
        FROM meal m
        JOIN meal_item mi ON mi.meal_id = m.id
        JOIN food_item fi ON fi.id = mi.food_id
        WHERE m.user_id = p_user_id AND m.meal_date = p_date
        GROUP BY m.user_id, m.meal_date
    ),
    hydration AS (
        SELECT 
            w.user_id,
            DATE(w.intake_datetime) AS w_date,
            COALESCE(SUM(w.quantity_ml), 0) AS total_water
        FROM water_intake w
        WHERE w.user_id = p_user_id AND DATE(w.intake_datetime) = p_date
        GROUP BY w.user_id, DATE(w.intake_datetime)
    )
    SELECT 
        p_user_id,
        p_date,
        COALESCE(n.cals, 0),
        COALESCE(n.prot, 0),
        COALESCE(n.crb, 0),
        COALESCE(n.ft, 0),
        COALESCE(h.total_water, 0)
    FROM (SELECT 1) dummy
    LEFT JOIN nutrition n ON 1=1
    LEFT JOIN hydration h ON 1=1;
END;
$$ LANGUAGE plpgsql;

-- Procedure Call Example:
-- SELECT * FROM sp_calculate_daily_macros(1, CURRENT_DATE);
*/


-- ----------------------------------------------------------------------------
-- 8. INDEX OPTIMIZATION VERIFICATION (EXPLAIN QUERY PLAN)
-- Demonstrates: Verification of B-Tree index scans vs. table scans
-- ----------------------------------------------------------------------------
EXPLAIN QUERY PLAN
SELECT * FROM users WHERE email = 'user@nutritrack.com';

EXPLAIN QUERY PLAN
SELECT * FROM meal WHERE user_id = 1 AND meal_date = CURRENT_DATE;

EXPLAIN QUERY PLAN
SELECT * FROM food_item WHERE name = 'Banana';
