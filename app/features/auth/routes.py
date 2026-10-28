from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from app.extensions import db
from app.models import ActivityLog, User
from app.core.security import is_safe_redirect_target
from .services import register_user


auth_bp = Blueprint("auth", __name__, template_folder="templates")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
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
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(request.form.get("password", "")) and user.is_active:
            login_user(user)
            db.session.add(ActivityLog(user_id=user.id, action="login", details="Successful login"))
            db.session.commit()
            next_target = request.args.get("next")
            if is_safe_redirect_target(next_target):
                return redirect(next_target)
            return redirect(url_for("dashboard.dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("dashboard.index"))
