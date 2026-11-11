from datetime import date
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from app.core.nutrition import round_nutrient
from app.core.security import is_safe_redirect_target
from app.extensions import db
from app.models import ActivityLog, WaterIntake


water_bp = Blueprint("water", __name__, template_folder="templates")


@water_bp.route("/water", methods=["GET", "POST"])
@login_required
def water():
    if request.method == "POST":
        try:
            quantity = float(request.form["quantity"])
            if quantity <= 0:
                raise ValueError
            db.session.add(WaterIntake(user_id=current_user.id, quantity_ml=quantity))
            db.session.add(ActivityLog(user_id=current_user.id, action="water_added", details=f"Quantity {quantity} ml"))
            db.session.commit()
            flash("Water intake saved.", "success")
        except (KeyError, ValueError):
            db.session.rollback()
            flash("Enter a quantity greater than zero.", "error")

        next_url = request.form.get("next")
        if next_url and is_safe_redirect_target(next_url):
            return redirect(next_url)

    entries = WaterIntake.query.filter_by(user_id=current_user.id).order_by(WaterIntake.intake_datetime.desc()).limit(20).all()
    total = sum(entry.quantity_ml for entry in entries if entry.intake_datetime.date() == date.today())
    return render_template("water/water.html", entries=entries, total=round_nutrient(total))


@water_bp.route("/water/<int:entry_id>/delete", methods=["POST"])
@login_required
def delete_water(entry_id):
    entry = WaterIntake.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    flash("Water entry deleted.", "success")
    return redirect(url_for("water.water"))
