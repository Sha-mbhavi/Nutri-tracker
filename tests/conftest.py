import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret-key-nutrition-tracker",
        "WTF_CSRF_ENABLED": False
    })
    with app.test_client() as client:
        yield client
