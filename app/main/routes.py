# app/main/routes.py
from flask import render_template, request
from flask_login import login_required, current_user

from . import bp
from app.models import DiaryEntry


@bp.route("/")
@bp.route("/index")
def index():
    # Introductory view logic
    return render_template("index.html")


@bp.route("/home")
@login_required
def home():
    # 1. Get the emotion_tag from the query parameters
    emotion_tag = request.args.get(
        "emotion_tag", None
    )  # Get 'emotion_tag', default to None if not present

    # Base query for the current user's diaries
    query = DiaryEntry.query.filter_by(owner_id=current_user.id)

    # 2. If emotion_tag is provided, add a filter to the query
    if emotion_tag:
        query = query.filter(DiaryEntry.dominant_emotion_label == emotion_tag)

    # Order the results and execute the query
    diaries = query.order_by(DiaryEntry.created_at.desc()).all()

    # 3. Pass the emotion_tag to the template
    return render_template(
        "dashboard/home.html",
        diaries=diaries,
        current_emotion_filter=emotion_tag,  # Pass the current filter to the template
    )


@bp.route("/shared")
@login_required
def shared():
    diaries = (
        DiaryEntry.query.filter(DiaryEntry.shared_with.any(id=current_user.id))
        .order_by(DiaryEntry.created_at.desc())
        .all()
    )
    return render_template("dashboard/shared.html", diaries=diaries)
