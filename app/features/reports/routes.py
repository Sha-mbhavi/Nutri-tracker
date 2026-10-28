import csv
import io
from datetime import date
from flask import Blueprint, Response, render_template, request
from flask_login import current_user, login_required
from app.features.dashboard.services import day_data

reports_bp = Blueprint("reports", __name__, template_folder="templates")

@reports_bp.route("/reports")
@login_required
def reports():
    return render_template("reports/reports.html")

@reports_bp.route("/reports/export.csv")
@login_required
def export_csv():
    start = date.fromisoformat(request.args.get("start", date.today().isoformat()))
    end = date.fromisoformat(request.args.get("end", date.today().isoformat()))
    if end < start:
        start, end = end, start
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["date", "calories", "protein", "carbs", "fat", "water_ml"])
    day = start
    while day <= end:
        totals, _, _ = day_data(current_user.id, day)
        writer.writerow([day.isoformat(), totals["calories"], totals["protein"], totals["carbs"], totals["fat"], totals["water"]])
        day = date.fromordinal(day.toordinal() + 1)
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=nutrition-report.csv"})
