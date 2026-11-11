import io
import json
import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from app.models import db, User, ActivityLog, Profile


@pytest.fixture
def client():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-oauth-secret-key",
        "GOOGLE_CLIENT_ID": None,
        "GOOGLE_CLIENT_SECRET": None,
        "GITHUB_CLIENT_ID": None,
        "GITHUB_CLIENT_SECRET": None,
    })
    with app.test_client() as client:
        yield client


def test_login_and_register_pages_contain_oauth_buttons(client):
    """Verify that both login and registration pages render clean OAuth buttons."""
    res_login = client.get("/login")
    assert res_login.status_code == 200
    assert b"Continue with Google" in res_login.data
    assert b"Continue with GitHub" in res_login.data
    assert b"/login/google" in res_login.data or b"/auth/login/google" in res_login.data
    assert b"/login/github" in res_login.data or b"/auth/login/github" in res_login.data

    res_register = client.get("/register")
    assert res_register.status_code == 200
    assert b"Continue with Google" in res_register.data
    assert b"Continue with GitHub" in res_register.data


def test_google_simulation_login_creates_user_and_logs_activity(client):
    """
    Test 1-click Google OAuth simulation mode when GOOGLE_CLIENT_ID is not configured.
    Verifies user creation, profile initialization, IP logging, and session authentication.
    """
    response = client.get("/auth/login/google", follow_redirects=True)
    assert response.status_code == 200
    assert b"Dashboard" in response.data or b"Welcome to NutriTrack" in response.data

    with client.application.app_context():
        user = User.query.filter_by(email="google.user@nutritrack.com").first()
        assert user is not None
        assert user.oauth_provider == "google"
        assert user.oauth_id == "google-demo-sub-1001"
        assert user.password_hash is not None
        # Passwordless security check: arbitrary passwords must fail
        assert not user.check_password("random_password_123")
        assert not user.check_password("")

        # Verify Profile was auto-provisioned
        profile = Profile.query.filter_by(user_id=user.id).first()
        assert profile is not None

        # Verify audit activity logging with client IP
        log = ActivityLog.query.filter_by(user_id=user.id, action="oauth_register").first()
        assert log is not None
        assert log.ip_address is not None
        assert "Google" in log.details


def test_github_simulation_login_and_subsequent_login(client):
    """
    Test GitHub OAuth simulation mode:
    1. First visit creates the user (oauth_register)
    2. Logging out and logging in again re-authenticates the existing user (oauth_login)
    """
    # 1. Initial registration via GitHub simulation
    res1 = client.get("/auth/login/github", follow_redirects=True)
    assert res1.status_code == 200

    with client.application.app_context():
        user = User.query.filter_by(email="github.user@nutritrack.com").first()
        assert user is not None
        assert user.oauth_provider == "github"
        assert user.oauth_id == "github-demo-id-2002"

    # Logout
    client.get("/logout")

    # 2. Subsequent login via GitHub simulation
    res2 = client.get("/auth/login/github", follow_redirects=True)
    assert res2.status_code == 200
    assert b"Welcome back" in res2.data

    with client.application.app_context():
        login_log = ActivityLog.query.filter_by(action="oauth_login").first()
        assert login_log is not None
        assert "github.user@nutritrack.com" in login_log.details


def test_oauth_simulation_callbacks_directly(client):
    """Verify that hitting the /auth/callback/ endpoints directly also succeeds in simulation mode."""
    res_google = client.get("/auth/callback/google", follow_redirects=True)
    assert res_google.status_code == 200
    client.get("/logout")

    res_github = client.get("/auth/callback/github", follow_redirects=True)
    assert res_github.status_code == 200


def test_oauth_account_linking_for_existing_email(client):
    """
    If a user previously registered with email/password, logging in via OAuth
    with the same email should link the provider credentials rather than creating a duplicate.
    """
    # Register regular email account
    client.post("/register", data={
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    client.get("/logout")

    # Simulate OAuth login with the same email
    from app.features.auth.routes import _complete_oauth_user
    with client.application.test_request_context():
        _complete_oauth_user(
            provider="google",
            oauth_id="google-jane-999",
            email="jane.doe@example.com",
            name="Jane Doe",
            client_ip="192.168.1.100"
        )

    with client.application.app_context():
        users = User.query.filter_by(email="jane.doe@example.com").all()
        assert len(users) == 1
        assert users[0].oauth_provider == "google"
        assert users[0].oauth_id == "google-jane-999"
        # Password hash remains intact so user can also still use password
        assert users[0].check_password("Password123!")


def test_oauth_safe_and_unsafe_redirect(client):
    """Verify safe redirect to internal targets and rejection of open redirects."""
    # Safe redirect
    res_safe = client.get("/auth/login/google?next=/reports", follow_redirects=False)
    assert res_safe.status_code == 302
    assert res_safe.headers["Location"].endswith("/reports")

    client.get("/logout")

    # Unsafe redirect to external domain must redirect to dashboard
    res_unsafe = client.get("/auth/login/google?next=https://malicious.evil.com", follow_redirects=False)
    assert res_unsafe.status_code == 302
    assert res_unsafe.headers["Location"].endswith("/dashboard")


def test_deactivated_oauth_user_is_rejected(client):
    """A deactivated account attempting OAuth login must be blocked."""
    # First create the user
    client.get("/auth/login/google", follow_redirects=True)
    with client.application.app_context():
        user = User.query.filter_by(email="google.user@nutritrack.com").first()
        user.is_active = False
        db.session.commit()
    client.get("/logout")

    # Attempt to log in again
    res = client.get("/auth/login/google", follow_redirects=True)
    assert b"This account has been deactivated" in res.data


def test_live_google_oauth_redirects_to_authorization_endpoint(client):
    """When GOOGLE_CLIENT_ID is configured, /auth/login/google redirects to Google."""
    client.application.config["GOOGLE_CLIENT_ID"] = "google-prod-client-id.apps.googleusercontent.com"
    res = client.get("/auth/login/google", follow_redirects=False)
    assert res.status_code == 302
    location = res.headers["Location"]
    assert location.startswith("https://accounts.google.com/o/oauth2/v2/auth")
    assert "client_id=google-prod-client-id.apps.googleusercontent.com" in location
    assert "response_type=code" in location
    assert "scope=openid+email+profile" in location


def test_live_github_oauth_redirects_to_authorization_endpoint(client):
    """When GITHUB_CLIENT_ID is configured, /auth/login/github redirects to GitHub."""
    client.application.config["GITHUB_CLIENT_ID"] = "github-prod-client-id"
    res = client.get("/auth/login/github", follow_redirects=False)
    assert res.status_code == 302
    location = res.headers["Location"]
    assert location.startswith("https://github.com/login/oauth/authorize")
    assert "client_id=github-prod-client-id" in location
    assert "scope=read%3Auser+user%3Aemail" in location


def test_live_google_callback_flow_with_mocked_endpoints(client):
    """Test full live callback token exchange and profile retrieval using mock responses."""
    client.application.config["GOOGLE_CLIENT_ID"] = "prod-client-id"
    client.application.config["GOOGLE_CLIENT_SECRET"] = "prod-client-secret"

    # Start login to set oauth_state in session
    client.get("/auth/login/google")
    with client.session_transaction() as sess:
        state = sess.get("oauth_state")

    token_response = json.dumps({"access_token": "mock-access-token"}).encode("utf-8")
    userinfo_response = json.dumps({
        "id": "google-live-sub-456",
        "email": "live.user@example.com",
        "name": "Live Google User"
    }).encode("utf-8")

    def mock_urlopen(req, timeout=10):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        mock_resp = MagicMock()
        if "oauth2.googleapis.com/token" in url:
            mock_resp.read.return_value = token_response
        elif "googleapis.com/oauth2/v2/userinfo" in url:
            mock_resp.read.return_value = userinfo_response
        mock_resp.__enter__.return_value = mock_resp
        return mock_resp

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        res = client.get(f"/auth/callback/google?code=valid-auth-code&state={state}", follow_redirects=True)
        assert res.status_code == 200

    with client.application.app_context():
        user = User.query.filter_by(email="live.user@example.com").first()
        assert user is not None
        assert user.oauth_provider == "google"
        assert user.oauth_id == "google-live-sub-456"
        assert user.name == "Live Google User"


def test_live_oauth_callback_state_mismatch_fails(client):
    """OAuth callback must reject invalid or missing CSRF state tokens."""
    client.application.config["GOOGLE_CLIENT_ID"] = "prod-client-id"
    client.application.config["GOOGLE_CLIENT_SECRET"] = "prod-client-secret"

    # Request callback without starting login (no state in session)
    res = client.get("/auth/callback/google?code=some-code&state=bad-state", follow_redirects=True)
    assert b"Invalid or expired OAuth state token" in res.data


def test_live_oauth_callback_provider_error(client):
    """OAuth callback should gracefully handle error responses from provider."""
    client.application.config["GOOGLE_CLIENT_ID"] = "prod-client-id"
    client.application.config["GOOGLE_CLIENT_SECRET"] = "prod-client-secret"

    res = client.get("/auth/callback/google?error=access_denied", follow_redirects=True)
    assert b"Google login was cancelled or failed" in res.data
