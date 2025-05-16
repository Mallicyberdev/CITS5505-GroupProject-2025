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
    # 1. Get filter and sort parameters from the query string
    emotion_tag = request.args.get("emotion_tag", None)
    sort_by_param = request.args.get("sort_by", "created_desc")  # Default sort
    search_query = request.args.get("search", None)  # For server-side search

    # Base query for the current user's diaries
    query = DiaryEntry.query.filter_by(owner_id=current_user.id)

    # 2. Apply emotion filter if provided
    if emotion_tag:
        query = query.filter(DiaryEntry.dominant_emotion_label == emotion_tag)

    # 3. Apply search filter if provided (for server-side search)
    if search_query:
        # Basic search on title and content.
        # For more advanced search, consider Flask-WhooshAlchemy or similar.
        search_term = f"%{search_query}%"
        query = query.filter(
            (DiaryEntry.title.ilike(search_term))
            | (DiaryEntry.content.ilike(search_term))
        )

    # 4. Apply sorting based on sort_by_param
    if sort_by_param == "created_asc":
        query = query.order_by(DiaryEntry.created_at.asc())
    elif sort_by_param == "title_asc":
        query = query.order_by(DiaryEntry.title.asc())
    elif sort_by_param == "title_desc":
        query = query.order_by(DiaryEntry.title.desc())
    elif sort_by_param == "mood_asc":
        # Assuming dominant_emotion_score is a field you can sort by directly
        # Handle cases where it might be None if necessary, e.g., using nullsfirst() or nullslast()
        query = query.order_by(DiaryEntry.dominant_emotion_score.asc().nullslast())
    elif sort_by_param == "mood_desc":
        query = query.order_by(DiaryEntry.dominant_emotion_score.desc().nullsfirst())
    else:  # Default sort (created_desc)
        query = query.order_by(DiaryEntry.created_at.desc())
        sort_by_param = "created_desc"  # Ensure default is reflected in template

    # Get page number for pagination (if you implement it)
    # page = request.args.get('page', 1, type=int)
    # diaries_paginated = query.paginate(page=page, per_page=9) # Example: 9 diaries per page
    # diaries = diaries_paginated.items

    # For now, without pagination, just get all matching diaries
    diaries = query.all()

    return render_template(
        "dashboard/home.html",
        diaries=diaries,
        # diaries_paginated=diaries_paginated, # If using pagination
        current_emotion_filter=emotion_tag,
        current_sort_by=sort_by_param,  # Pass the current sort option
        # current_search_query=search_query # If using server-side search
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
