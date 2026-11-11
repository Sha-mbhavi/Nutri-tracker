import csv
import io
import json
from datetime import date
from flask import Blueprint, Response, render_template, request, flash, redirect, url_for, jsonify
from flask_login import current_user, login_required
from app.features.dashboard.services import day_data
from app.models import ActivityLog, db, Meal, WaterIntake, Goal
from app.core.azure_blob import blob_service
from app.core.security import get_client_ip

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
    
    # Audit log
    db.session.add(ActivityLog(
        user_id=current_user.id,
        action="export_csv_report",
        details=f"Exported CSV report from {start} to {end}",
        ip_address=get_client_ip()
    ))
    db.session.commit()

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=nutrition-report-{current_user.id}-{start}-to-{end}.csv"}
    )

@reports_bp.route("/reports/export.json")
@login_required
def export_json():
    """
    DP-900 Semi-Structured Data Export:
    Extracts relational nutrition data and serializes it into a semi-structured JSON document
    suitable for Azure Cosmos DB / NoSQL document processing.
    """
    start = date.fromisoformat(request.args.get("start", date.today().isoformat()))
    end = date.fromisoformat(request.args.get("end", date.today().isoformat()))
    if end < start:
        start, end = end, start

    records = []
    day = start
    while day <= end:
        totals, meals, _ = day_data(current_user.id, day)
        meals_payload = []
        for meal in meals:
            meals_payload.append({
                "meal_id": meal.id,
                "meal_type": meal.meal_type,
                "items": [{
                    "item_id": item.id,
                    "food_id": item.food_id,
                    "food_name": item.food.name,
                    "quantity_g": item.quantity,
                    "calories": round(item.food.calories * item.quantity / 100.0, 2),
                    "protein": round(item.food.protein * item.quantity / 100.0, 2),
                    "carbs": round(item.food.carbs * item.quantity / 100.0, 2),
                    "fat": round(item.food.fat * item.quantity / 100.0, 2),
                    "fiber": round(item.food.fiber * item.quantity / 100.0, 2)
                } for item in meal.items]
            })

        records.append({
            "date": day.isoformat(),
            "daily_totals": totals,
            "meals": meals_payload
        })
        day = date.fromordinal(day.toordinal() + 1)

    export_payload = {
        "export_metadata": {
            "document_type": "NutriTrack Dataset Export",
            "format_version": "1.0",
            "user_id": current_user.id,
            "user_name": current_user.name,
            "range": {"start": start.isoformat(), "end": end.isoformat()}
        },
        "daily_records": records
    }

    # Audit log
    db.session.add(ActivityLog(
        user_id=current_user.id,
        action="export_json_report",
        details=f"Exported semi-structured JSON document from {start} to {end}",
        ip_address=get_client_ip()
    ))
    db.session.commit()

    return Response(
        json.dumps(export_payload, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename=nutrition-data-{current_user.id}.json"}
    )

@reports_bp.route("/reports/archive-blob", methods=["POST"])
@login_required
def archive_to_azure_blob():
    """
    DP-900 Cloud Non-Relational Store (Azure Blob Storage):
    Archives the user's nutritional report into an Azure Blob Storage container.
    """
    start_str = request.form.get("start", date.today().isoformat())
    end_str = request.form.get("end", date.today().isoformat())
    start = date.fromisoformat(start_str)
    end = date.fromisoformat(end_str)
    if end < start:
        start, end = end, start

    # Prepare document content
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["date", "calories", "protein", "carbs", "fat", "water_ml"])
    day = start
    while day <= end:
        totals, _, _ = day_data(current_user.id, day)
        writer.writerow([day.isoformat(), totals["calories"], totals["protein"], totals["carbs"], totals["fat"], totals["water"]])
        day = date.fromordinal(day.toordinal() + 1)

    filename = f"report_user_{current_user.id}_{start.isoformat()}_{end.isoformat()}.csv"
    result = blob_service.upload_blob(filename, output.getvalue(), content_type="text/csv")

    # Record activity log
    db.session.add(ActivityLog(
        user_id=current_user.id,
        action="azure_blob_archive",
        details=f"Archived report to Azure Blob Storage ({result.get('storage_provider')}) filename: {filename}",
        ip_address=get_client_ip()
    ))
    db.session.commit()

    flash(f"Report archived to {result.get('storage_provider')}. Container: {result.get('container')}, File: {filename}", "success")
    return render_template("reports/reports.html", blob_result=result)
