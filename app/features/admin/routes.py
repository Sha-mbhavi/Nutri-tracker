from flask import Blueprint, render_template
from flask_login import login_required
from app.core.permissions import admin_required
from app.models import ActivityLog, FoodItem


admin_bp = Blueprint("admin", __name__, template_folder="templates")


@admin_bp.route("/admin")
@login_required
@admin_required
def admin():
    return render_template("admin/admin.html", foods=FoodItem.query.order_by(FoodItem.name).all(),
                           logs=ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(50).all())
