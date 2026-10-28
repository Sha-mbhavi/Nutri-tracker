# NutriTrack Architecture

## Overview

NutriTrack is a Flask application organized around product features. Shared infrastructure lives in `app/core/` and `app/extensions.py`; business capabilities live in independent packages under `app/features/`.

## Application structure

```text
Nutri-tracker/
├── app.py                 # Development entry point
├── config.py              # Environment-backed configuration
├── app/
│   ├── __init__.py        # Application factory and blueprint registration
│   ├── extensions.py      # Flask-SQLAlchemy and Flask-Login extensions
│   ├── models.py          # SQLAlchemy database models
│   ├── core/
│   │   ├── errors.py      # Application error handlers
│   │   ├── nutrition.py   # Shared nutrition calculations
│   │   ├── permissions.py # Authorization helpers
│   │   └── security.py    # Redirect and security helpers
│   ├── features/
│   │   ├── auth/          # Registration, login, and logout
│   │   ├── profile/       # Personal profile management
│   │   ├── food_catalog/  # Food search and catalog
│   │   ├── meals/         # Meal entry and history
│   │   ├── nutrition/     # Nutrition goals
│   │   ├── water/         # Water intake tracking
│   │   ├── reminders/     # User reminders
│   │   ├── dashboard/     # Personalized dashboard and landing page
│   │   ├── wellness/      # Wellness recommendations
│   │   └── admin/         # Administrator access
│   ├── templates/
│   │   └── base.html      # Shared application layout
│   └── static/
│       ├── css/
│       └── js/
├── database/schema.sql
├── instance/
└── tests/
```

## Feature package layout

Each implemented feature is separated into its own Flask blueprint package:

```text
feature/
├── __init__.py
├── routes.py       # HTTP routes and request handling
├── services.py     # Feature-specific business logic
└── templates/
    └── feature/    # Feature-local HTML templates
```

Routes remain thin and delegate validation and reusable behavior to services where appropriate. Feature templates are rendered with their blueprint-local template paths.

## Request flow

1. `app.py` creates the application through `create_app()`.
2. The application factory loads configuration and initializes shared extensions.
3. Feature blueprints are registered with Flask.
4. A request is matched to a feature route.
5. Authentication and authorization helpers protect private routes.
6. Models persist or retrieve the current user's data through SQLAlchemy.
7. The route renders a feature template using the shared base layout.

## Authentication and authorization

Flask-Login manages authenticated sessions. User loading is provided by `app/extensions.py` and configured in the application factory. Routes containing personal nutrition data use `@login_required`. Administrator-only access is enforced by a shared permission decorator in `app/core/permissions.py`.

## Data ownership

Nutrition records reference the owning user through `user_id` foreign keys. Feature queries must scope meals, water, goals, reminders, and other private data to the authenticated user. Shared catalog records remain accessible to authenticated users.

## Configuration and persistence

Configuration is defined in `config.py` and may be overridden by environment variables for the secret key, database URL, and secure session cookie. SQLAlchemy creates and manages models, while `database/schema.sql` documents SQLite views, joins, and indexes.

## Testing

Tests are organized under `tests/` and run through pytest. Tests use an isolated in-memory SQLite database and verify registration, login, profile management, meal calculations, protected routes, and existing feature behavior.

## Existing-feature principle

The modular structure must preserve established URLs and templates. New features should be added as blueprints without moving existing routes into monolithic application code. Shared changes must remain backward-compatible with current tests and user-facing behavior.
