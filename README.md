# NutriTrack

NutriTrack is a Flask wellness application for recording meals, nutrition targets, water intake, and reminders. It is not a medical diagnosis or treatment system.

## Features

- Registration, login, secure password hashing, logout, and protected pages
- Food search from a seeded nutrition catalog
- Meal and gram-based portion logging with calculated totals
- Water and goal tracking
- Daily dashboard and rule-based wellness prompts
- Reminders, profile management, and restricted administrator view
- SQLite development database and SQLAlchemy models

## Local setup

```powershell
cd C:\Users\nitus\Nutri-tracker
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. The SQLite database is created automatically in the instance directory and a small sample catalog is seeded.

## Configuration

- `SECRET_KEY`: replace the development key in production.
- `DATABASE_URL`: SQLAlchemy connection URL. The default is SQLite for local development.
- `SESSION_COOKIE_SECURE`: set to `true` in production when the application is served over HTTPS.

Production deployments must use HTTPS and secure session-cookie settings.

## Tests

```powershell
python -m pytest -q
```

## Nutrition calculation

Only `100g` basis is implemented in the MVP. Nutrients are calculated as `food value × quantity(g) ÷ 100`. Values are rounded to two decimal places using half-up rounding, with daily meal totals calculated from persisted meal items. Serving-unit conversion is intentionally documented as out of scope until completed.

## Data safety

Personal nutrition data is private to the owning user. Catalog administration is limited to users with the `admin` role. Do not use real health records in demonstrations; use synthetic data.

## Repository structure

- `app.py` Flask development entry point
- `config.py` environment-backed application configuration
- `app/extensions.py` shared database and login extensions
- `app/models.py` SQLAlchemy models
- `app/core/` shared security, permissions, nutrition, and error helpers
- `app/features/` route and service modules organized by product feature
- `app/templates/` shared layout and components
- `app/static/` shared styles and scripts
- `tests/` pytest coverage
- `database/schema.sql` SQL view, JOIN, and index examples

Feature packages follow the `routes.py`, `services.py`, and feature-local template structure shown in the project architecture.
