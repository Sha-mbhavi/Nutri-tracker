from flask import Blueprint, flash, render_template, request
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Profile
from .services import parse_profile_form

profile_bp = Blueprint("profile", __name__, template_folder="templates")


@profile_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if not current_user.profile:
        current_user.profile = Profile()
        db.session.flush()
    if request.method == "POST":
        try:
            for field, value in parse_profile_form(request.form).items():
                setattr(current_user.profile, field, value)
            db.session.commit()
            flash("Profile updated.", "success")
        except (TypeError, ValueError):
            db.session.rollback()
            flash("Enter valid profile values. Height, weight, and date of birth can be left blank.", "error")
    return render_template("profile/profile.html")
