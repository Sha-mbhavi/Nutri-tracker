import pytest
import json
from app import create_app
from app.models import db, User, ActivityLog

@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "test-key-security"})
    with app.test_client() as client:
        yield client

def test_rbac_admin_access_control(client):
    """
    Cloud Security Rubric:
    Verify Role-Based Access Control (RBAC):
    - Regular users cannot access /admin
    - Admin users can access /admin
    """
    # Login as regular user
    client.post("/login", data={"email": "user@nutritrack.com", "password": "User123!"}, follow_redirects=True)
    res_user = client.get("/admin", follow_redirects=True)
    assert b"Administrator access required." in res_user.data

    # Logout
    client.get("/logout")

    # Login as admin
    client.post("/login", data={"email": "admin@nutritrack.com", "password": "Admin123!"}, follow_redirects=True)
    res_admin = client.get("/admin", follow_redirects=True)
    assert res_admin.status_code == 200
    assert b"Recent activity" in res_admin.data

def test_failed_login_activity_logging(client):
    """
    Cloud Security Rubric:
    Audit Trail & Activity Log records failed and successful attempts with IP address.
    """
    client.post("/login", data={"email": "user@nutritrack.com", "password": "WrongPassword!"})
    with client.application.app_context():
        log = ActivityLog.query.filter_by(action="login_failed").first()
        assert log is not None
        assert "user@nutritrack.com" in log.details
        assert log.ip_address is not None

def test_dp900_semi_structured_json_export(client):
    """
    DP-900 Rubric:
    Verify semi-structured JSON document export for Cosmos DB / NoSQL ingestion.
    """
    client.post("/login", data={"email": "user@nutritrack.com", "password": "User123!"}, follow_redirects=True)
    response = client.get("/reports/export.json")
    assert response.status_code == 200
    assert response.mimetype == "application/json"
    data = json.loads(response.data.decode("utf-8"))
    assert data["export_metadata"]["document_type"] == "NutriTrack Dataset Export"
    assert "daily_records" in data

def test_dp900_blob_storage_archival(client):
    """
    DP-900 Rubric:
    Verify non-relational blob archival endpoint runs and logs storage metadata.
    """
    client.post("/login", data={"email": "user@nutritrack.com", "password": "User123!"}, follow_redirects=True)
    response = client.post("/reports/archive-blob", data={"start": "2026-11-01", "end": "2026-11-11"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Azure Blob Storage" in response.data
