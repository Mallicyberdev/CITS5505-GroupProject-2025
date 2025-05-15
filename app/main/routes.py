# app/main/routes.py
from flask import render_template
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
    diaries = (
        DiaryEntry.query.filter_by(owner_id=current_user.id)
        .order_by(DiaryEntry.created_at.desc())
        .all()
    )
    return render_template("dashboard/home.html", diaries=diaries)


@bp.route("/shared")
@login_required
def shared():
    diaries = (
        DiaryEntry.query.filter(DiaryEntry.shared_with.any(id=current_user.id))
        .order_by(DiaryEntry.created_at.desc())
        .all()
    )
    return render_template("dashboard/shared.html", diaries=diaries)
