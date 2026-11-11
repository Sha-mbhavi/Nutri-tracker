import os
import json
import secrets
import urllib.parse
import urllib.request
import urllib.error
from datetime import date
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from app.extensions import db
from app.models import ActivityLog, Goal, Profile, User
from app.core.security import is_safe_redirect_target, get_client_ip
from .services import register_user


auth_bp = Blueprint("auth", __name__, template_folder="templates")


def _complete_oauth_user(provider, oauth_id, email, name, client_ip, next_url=None, simulation=False):
    """
    Finds or registers an OAuth-authenticated user, initializes profile and goals if new,
    records activity in ActivityLog with client IP, and signs user in.
    """
    if not email:
        flash(f"Could not retrieve email address from {provider.title()}.", "error")
        return redirect(url_for("auth.login"))

    email = email.strip().lower()
    user = User.query.filter_by(oauth_provider=provider, oauth_id=str(oauth_id)).first()
    is_new = False

    if not user:
        # Check if an existing account exists with the same email
        user = User.query.filter_by(email=email).first()
        if user:
            user.oauth_provider = provider
            user.oauth_id = str(oauth_id)
            if not user.password_hash:
                user.set_password(secrets.token_urlsafe(32))
            if not user.name and name:
                user.name = name
        else:
            is_new = True
            user = User(
                name=name or email.split("@")[0].title(),
                email=email,
                oauth_provider=provider,
                oauth_id=str(oauth_id),
                role="user",
                is_active=True
            )
            # Generate unguessable random password hash to satisfy database non-null constraints
            user.set_password(secrets.token_urlsafe(32))
            db.session.add(user)
            db.session.flush()

            profile = Profile(
                user_id=user.id,
                diet_preference="Balanced",
                nutrition_goal="Maintenance"
            )
            db.session.add(profile)

            # Ensure active nutritional goal is provisioned for clean dashboard metrics
            goal = Goal(
                user_id=user.id,
                target_calories=2100.0,
                target_protein=120.0,
                target_carbs=240.0,
                target_fat=65.0,
                target_fiber=30.0,
                target_water_ml=2500.0,
                start_date=date.today(),
                status="active"
            )
            db.session.add(goal)

    if not user.is_active:
        flash("This account has been deactivated. Please contact support.", "error")
        return redirect(url_for("auth.login"))

    sim_tag = " (Simulation Mode)" if simulation else ""
    if is_new:
        action = "oauth_register"
        details = f"User registered via {provider.title()} OAuth{sim_tag}: {email}"
        flash(f"Welcome to NutriTrack! Logged in with {provider.title()}{sim_tag}.", "success")
    else:
        action = "oauth_login"
        details = f"User logged in via {provider.title()} OAuth{sim_tag}: {email}"
        flash(f"Welcome back! Logged in with {provider.title()}{sim_tag}.", "success")

    db.session.add(ActivityLog(
        user_id=user.id,
        action=action,
        details=details,
        ip_address=client_ip
    ))
    db.session.commit()
    login_user(user)

    if next_url and is_safe_redirect_target(next_url):
        return redirect(next_url)
    return redirect(url_for("dashboard.dashboard"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        client_ip = get_client_ip()
        if not name or email.count("@") != 1 or not all(email.split("@", 1)) or "." not in email.rsplit("@", 1)[-1]:
            flash("Enter your name and a valid email address.", "error")
        elif len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
        elif password != confirm_password:
            flash("Passwords do not match.", "error")
        elif User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
        else:
            user, error = register_user(name, email, password)
            if error:
                flash(error, "error")
            else:
                db.session.add(ActivityLog(user_id=user.id, action="register", details=f"User registered with email {email}", ip_address=client_ip))
                db.session.commit()
                login_user(user)
                flash("Welcome to NutriTrack!", "success")
                return redirect(url_for("dashboard.dashboard"))
    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        client_ip = get_client_ip()
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            db.session.add(ActivityLog(user_id=user.id, action="login", details="Successful login", ip_address=client_ip))
            db.session.commit()
            next_target = request.args.get("next")
            if is_safe_redirect_target(next_target):
                return redirect(next_target)
            return redirect(url_for("dashboard.dashboard"))
        
        # Log failed login attempt for security audit trail
        db.session.add(ActivityLog(user_id=user.id if user else None, action="login_failed", details=f"Failed login attempt for {email}", ip_address=client_ip))
        db.session.commit()
        flash("Invalid email or password.", "error")
    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    client_ip = get_client_ip()
    db.session.add(ActivityLog(user_id=current_user.id, action="logout", details="User logged out", ip_address=client_ip))
    db.session.commit()
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("dashboard.index"))


# -----------------------------------------------------------------------------
# Google OAuth Routes
# -----------------------------------------------------------------------------
@auth_bp.route("/auth/login/google")
@auth_bp.route("/login/google", endpoint="login_google_alias")
def oauth_login_google():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    client_id = os.getenv("GOOGLE_CLIENT_ID") or current_app.config.get("GOOGLE_CLIENT_ID")
    next_target = request.args.get("next")
    if next_target:
        session["oauth_next"] = next_target

    # Development / Simulation Mode
    if not client_id:
        return _complete_oauth_user(
            provider="google",
            oauth_id="google-demo-sub-1001",
            email="google.user@nutritrack.com",
            name="Google User",
            client_ip=get_client_ip(),
            next_url=session.pop("oauth_next", None) or next_target,
            simulation=True
        )

    # Live Production OAuth2 Flow
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state
    redirect_uri = url_for("auth.oauth_callback_google", _external=True)
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online"
    }
    return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}")


@auth_bp.route("/auth/callback/google")
@auth_bp.route("/callback/google", endpoint="callback_google_alias")
def oauth_callback_google():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    client_id = os.getenv("GOOGLE_CLIENT_ID") or current_app.config.get("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET") or current_app.config.get("GOOGLE_CLIENT_SECRET")

    # Simulation fallback if callback accessed directly without credentials
    if not client_id or not client_secret:
        return _complete_oauth_user(
            provider="google",
            oauth_id="google-demo-sub-1001",
            email="google.user@nutritrack.com",
            name="Google User",
            client_ip=get_client_ip(),
            next_url=session.pop("oauth_next", None),
            simulation=True
        )

    error = request.args.get("error")
    if error:
        flash(f"Google login was cancelled or failed: {error}", "error")
        return redirect(url_for("auth.login"))

    code = request.args.get("code")
    state = request.args.get("state")
    saved_state = session.pop("oauth_state", None)

    if not state or state != saved_state or not code:
        flash("Invalid or expired OAuth state token. Please try logging in again.", "error")
        return redirect(url_for("auth.login"))

    redirect_uri = url_for("auth.oauth_callback_google", _external=True)
    try:
        token_payload = urllib.parse.urlencode({
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }).encode("utf-8")
        token_req = urllib.request.Request(
            "https://oauth2.googleapis.com/token",
            data=token_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        with urllib.request.urlopen(token_req, timeout=10) as resp:
            token_data = json.loads(resp.read().decode("utf-8"))

        access_token = token_data.get("access_token")
        if not access_token:
            flash("Failed to obtain access token from Google.", "error")
            return redirect(url_for("auth.login"))

        userinfo_req = urllib.request.Request(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        with urllib.request.urlopen(userinfo_req, timeout=10) as resp:
            user_data = json.loads(resp.read().decode("utf-8"))

        email = user_data.get("email")
        name = user_data.get("name")
        oauth_id = user_data.get("id")

        return _complete_oauth_user(
            provider="google",
            oauth_id=oauth_id,
            email=email,
            name=name,
            client_ip=get_client_ip(),
            next_url=session.pop("oauth_next", None),
            simulation=False
        )
    except Exception as exc:
        current_app.logger.error(f"Google OAuth error: {exc}")
        flash("Authentication with Google encountered an error. Please try again.", "error")
        return redirect(url_for("auth.login"))


# -----------------------------------------------------------------------------
# GitHub OAuth Routes
# -----------------------------------------------------------------------------
@auth_bp.route("/auth/login/github")
@auth_bp.route("/login/github", endpoint="login_github_alias")
def oauth_login_github():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    client_id = os.getenv("GITHUB_CLIENT_ID") or current_app.config.get("GITHUB_CLIENT_ID")
    next_target = request.args.get("next")
    if next_target:
        session["oauth_next"] = next_target

    # Development / Simulation Mode
    if not client_id:
        return _complete_oauth_user(
            provider="github",
            oauth_id="github-demo-id-2002",
            email="github.user@nutritrack.com",
            name="GitHub User",
            client_ip=get_client_ip(),
            next_url=session.pop("oauth_next", None) or next_target,
            simulation=True
        )

    # Live Production OAuth2 Flow
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state
    redirect_uri = url_for("auth.oauth_callback_github", _external=True)
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "read:user user:email",
        "state": state
    }
    return redirect(f"https://github.com/login/oauth/authorize?{urllib.parse.urlencode(params)}")


@auth_bp.route("/auth/callback/github")
@auth_bp.route("/callback/github", endpoint="callback_github_alias")
def oauth_callback_github():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    client_id = os.getenv("GITHUB_CLIENT_ID") or current_app.config.get("GITHUB_CLIENT_ID")
    client_secret = os.getenv("GITHUB_CLIENT_SECRET") or current_app.config.get("GITHUB_CLIENT_SECRET")

    # Simulation fallback if callback accessed directly without credentials
    if not client_id or not client_secret:
        return _complete_oauth_user(
            provider="github",
            oauth_id="github-demo-id-2002",
            email="github.user@nutritrack.com",
            name="GitHub User",
            client_ip=get_client_ip(),
            next_url=session.pop("oauth_next", None),
            simulation=True
        )

    error = request.args.get("error")
    if error:
        flash(f"GitHub login was cancelled or failed: {error}", "error")
        return redirect(url_for("auth.login"))

    code = request.args.get("code")
    state = request.args.get("state")
    saved_state = session.pop("oauth_state", None)

    if not state or state != saved_state or not code:
        flash("Invalid or expired OAuth state token. Please try logging in again.", "error")
        return redirect(url_for("auth.login"))

    redirect_uri = url_for("auth.oauth_callback_github", _external=True)
    try:
        token_payload = json.dumps({
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri
        }).encode("utf-8")
        token_req = urllib.request.Request(
            "https://github.com/login/oauth/access_token",
            data=token_payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"}
        )
        with urllib.request.urlopen(token_req, timeout=10) as resp:
            token_data = json.loads(resp.read().decode("utf-8"))

        access_token = token_data.get("access_token")
        if not access_token:
            flash("Failed to obtain access token from GitHub.", "error")
            return redirect(url_for("auth.login"))

        userinfo_req = urllib.request.Request(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}", "User-Agent": "NutriTrack-OAuth"}
        )
        with urllib.request.urlopen(userinfo_req, timeout=10) as resp:
            github_user = json.loads(resp.read().decode("utf-8"))

        oauth_id = str(github_user.get("id"))
        name = github_user.get("name") or github_user.get("login")
        email = github_user.get("email")

        if not email:
            emails_req = urllib.request.Request(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}", "User-Agent": "NutriTrack-OAuth"}
            )
            with urllib.request.urlopen(emails_req, timeout=10) as resp:
                emails_list = json.loads(resp.read().decode("utf-8"))
                for entry in emails_list:
                    if entry.get("primary") and entry.get("verified"):
                        email = entry.get("email")
                        break
                if not email and emails_list:
                    email = emails_list[0].get("email")

        return _complete_oauth_user(
            provider="github",
            oauth_id=oauth_id,
            email=email,
            name=name,
            client_ip=get_client_ip(),
            next_url=session.pop("oauth_next", None),
            simulation=False
        )
    except Exception as exc:
        current_app.logger.error(f"GitHub OAuth error: {exc}")
        flash("Authentication with GitHub encountered an error. Please try again.", "error")
        return redirect(url_for("auth.login"))
