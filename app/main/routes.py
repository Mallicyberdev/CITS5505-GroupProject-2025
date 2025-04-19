# app/main/routes.py
from flask import render_template
from . import bp


@bp.route("/")
@bp.route("/index")
def index():
    # Introductory view logic
    return render_template("index.html")
