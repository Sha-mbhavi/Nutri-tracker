from flask import Blueprint, render_template, request
from flask_login import login_required

voice_bp = Blueprint("voice", __name__, template_folder="templates")

@voice_bp.route("/voice")
@login_required
def voice():
    return render_template("voice/voice.html")


@voice_bp.route("/scan", methods=["GET", "POST"])
@login_required
def scan_food():
    suggestions = []
    if request.method == "POST":
        photo = request.files.get("photo")
        if photo and photo.filename:
            suggestions = ["Rice", "Dal", "Vegetables"]
        else:
            suggestions = []
    return render_template("voice/scan.html", suggestions=suggestions)
