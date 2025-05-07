# app/main/routes.py
from flask import render_template
from flask_login import login_required, current_user
from sqlalchemy import or_

from . import bp
from ..models import DiaryEntry


@bp.route("/")
@bp.route("/index")
def index():
    # Introductory view logic
    return render_template("index.html")


@bp.route("/home")
@login_required
def home():
    diaries = DiaryEntry.for_user(current_user.id).order_by().all()
    return render_template("home.html", diaries=diaries)
