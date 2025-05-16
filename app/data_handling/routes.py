"""
Routes for diary entry management and emotion analysis.

This module handles CRUD operations for diary entries and
implements emotion analysis using transformer models.
"""

# routes.py
from flask import request, render_template, flash, url_for, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import redirect
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, case
from app import db
from app.models import User, DiaryEntry
from . import bp
from .forms import DiaryForm

from transformers import pipeline

emotion_classifier = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    top_k=None,
)

POSITIVE_EMOTIONS = {
    "joy",
    "surprise",
}

NEGATIVE_EMOTIONS = {
    "anger",
    "sadness",
    "fear",
    "disgust",
}


@bp.route("/create_diary", methods=["GET", "POST"])
@login_required
def create_diary():
    """Create a new diary entry.

    Returns:
        GET: Render diary creation form
        POST: Redirect to home page after creating entry

    Requires:
        User authentication
    """
    form = DiaryForm()
    if form.validate_on_submit():  # Handles POST and validation
        new_diary = DiaryEntry(
            title=form.title.data,
            content=form.content.data,
            owner_id=current_user.id,
        )
        result = emotion_classifier(new_diary.content)

        new_diary.update_emotion_analysis(result)

        db.session.add(new_diary)
        db.session.commit()

        flash("Diary created and analyzed successfully!", "success")
        return redirect(url_for("main.home"))  # Or your main diary list page

    # For GET request, or if form validation fails on POST
    return render_template(
        "dashboard/upload.html", title="Create Diary Entry", form=form
    )


@bp.route("/view_diary/<diary_id>")
@login_required
def view_diary(diary_id):
    diary_entry = DiaryEntry.query.get_or_404(diary_id)
    if diary_entry.owner_id != current_user.id and not diary_entry.is_shared_with_user(
        current_user
    ):
        flash("You do not have permission to view this diary entry.", "danger")
        return redirect(url_for("main.home"))

    diary_entry.content = diary_entry.content.replace("\r\n", "<br>").replace(
        "\n", "<br>"
    )

    return render_template(
        "dashboard/details.html", title="View Diary Entry", diary_entry=diary_entry
    )


@bp.route("/edit_diary/<int:diary_id>", methods=["GET", "POST"])
@login_required
def edit_diary(diary_id):
    diary_entry = db.session.get(DiaryEntry, diary_id)
    if not diary_entry:
        flash("Diary entry not found.", "warning")
        return redirect(url_for("main.home"))  # Or your main diary list page

    if diary_entry.owner_id != current_user.id:
        flash("You do not have permission to edit this diary entry.", "danger")
        return redirect(url_for("main.home"))

    form = DiaryForm(
        obj=diary_entry
    )  # Pre-populate form with existing diary_entry data

    if form.validate_on_submit():  # This handles POST request and validation
        # Update the diary_entry object with form data
        diary_entry.title = form.title.data

        # Perform emotion analysis on the updated content
        if form.content.data != diary_entry.content:
            diary_entry.content = form.content.data
            result = emotion_classifier(diary_entry.content)
            diary_entry.update_emotion_analysis(result)

        try:
            db.session.commit()
            flash("Diary entry updated successfully!", "success")
            # Redirect to the view page of the edited diary
            return redirect(
                url_for("data_handling.view_diary", diary_id=diary_entry.id)
            )
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating diary entry: {str(e)}", "danger")
            # Log the error e for debugging

    prev_url = request.referrer or url_for("main.home", diary_id=diary_entry.id)
    # For GET request, or if form validation failed on POST, render the edit form
    return render_template(
        "dashboard/edit.html",
        title="Edit Diary Entry",
        form=form,
        diary_entry=diary_entry,
        prev_url=prev_url,
    )


@bp.route("/delete_diary/<int:diary_id>", methods=["POST"])
@login_required
def delete_diary(diary_id):
    diary_entry = db.session.get(DiaryEntry, diary_id)
    if not diary_entry:
        flash("Diary entry not found.", "warning")
        return redirect(url_for("main.home"))

    if diary_entry.owner_id != current_user.id:
        flash("You do not have permission to delete this diary entry.", "danger")
        return redirect(url_for("data_handling.view_diary", diary_id=diary_id))

    try:
        db.session.delete(diary_entry)
        db.session.commit()
        flash("Diary entry deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting diary entry: {str(e)}", "danger")

    return redirect(url_for("main.home"))


@bp.route("/share_diary/<int:diary_id>", methods=["POST"])
@login_required
def share_diary(diary_id):
    diary_entry = DiaryEntry.query.get_or_404(diary_id)

    if diary_entry.owner_id != current_user.id:
        flash("You can only share diaries you own.", "danger")
        return redirect(url_for("main.home"))

    shared_usernames = request.form.getlist("shared_users")
    current_shared_users = {user.username for user in diary_entry.get_shared_users()}

    try:
        success_count = 0
        # Share with newly selected users
        for username in shared_usernames:
            if username not in current_shared_users:
                shared_user = User.query.filter_by(username=username).first()
                if not shared_user:
                    flash(f"User '{username}' not found.", "warning")
                    continue
                if diary_entry.share_with_user(shared_user):
                    success_count += 1

        # Unshare from users who were deselected
        for username in current_shared_users:
            if username not in shared_usernames:
                shared_user = User.query.filter_by(username=username).first()
                if shared_user and diary_entry.unshare_from_user(shared_user):
                    success_count += 1

        if success_count > 0:
            db.session.commit()
            flash(
                f"Diary sharing updated successfully! {success_count} changes made.",
                "success",
            )
        else:
            flash("No changes made to sharing settings.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to update diary sharing: {str(e)}", "danger")

    return redirect(url_for("data_handling.view_diary", diary_id=diary_id))


@bp.route("/get_shared_users/<int:diary_id>", methods=["GET"])
@login_required
def get_shared_users(diary_id):
    diary_entry = DiaryEntry.query.get_or_404(diary_id)
    if diary_entry.owner_id != current_user.id:
        flash("You can only view shared users for diaries you own.", "danger")
        return jsonify([]), 403
    shared_users = diary_entry.get_shared_users()
    return jsonify(
        [{"id": user.id, "username": user.username} for user in shared_users]
    )


@bp.route("/mood-timeline", methods=["GET"])
@login_required
def mood_timeline():
    """
    Return a timeline of dominant emotions for the current user.

    Params:
        days (int, optional): How many days back to include (default: 30).

    Response format:
        [
            {"date": "2025-04-16", "emotion": "joy", "count": 2},
            {"date": "2025-04-16", "emotion": "sadness", "count": 1},
            ...
        ]
    """
    try:
        days = int(request.args.get("days", 30))
    except ValueError:
        days = 30

    tz = timezone(timedelta(hours=8))  # Australia/Perth (UTC+08:00)
    start_date = datetime.now(tz).replace(
        hour=0, minute=0, second=0, microsecond=0
    ) - timedelta(days=days - 1)

    # Aggregate counts by date and dominant emotion
    rows = (
        db.session.query(
            func.date(DiaryEntry.created_at).label("date"),
            DiaryEntry.dominant_emotion_label.label("emotion"),
            func.count().label("count"),
        )
        .filter(
            DiaryEntry.owner_id == current_user.id,
            DiaryEntry.dominant_emotion_label.isnot(None),
            DiaryEntry.created_at >= start_date,
        )
        .group_by(func.date(DiaryEntry.created_at), DiaryEntry.dominant_emotion_label)
        .order_by(func.date(DiaryEntry.created_at))
        .all()
    )

    # Convert to list of dicts for JSON output
    data = [
        {"date": str(row.date), "emotion": row.emotion, "count": row.count}
        for row in rows
    ]
    return jsonify(data)


@bp.route("/average-mood-index", methods=["GET"])
@login_required
def average_mood_index():
    """
    Calculate the average mood index for the last seven days (inclusive).

    Scoring:
        +1 for emotions in POSITIVE_EMOTIONS
        -1 for emotions in NEGATIVE_EMOTIONS
         0 for neutral / unknown

    Response format:
        {
            "start": "2025-05-09",
            "end":   "2025-05-15",
            "average_mood_index": 0.42
        }
    """
    tz = timezone(timedelta(hours=8))  # Australia/Perth (UTC+08:00)
    end_date = datetime.now(tz).replace(hour=23, minute=59, second=59, microsecond=0)
    start_date = end_date - timedelta(days=6)  # last 7 calendar days

    score_expr = case(
        (
            DiaryEntry.dominant_emotion_label.in_(POSITIVE_EMOTIONS),
            1,
        ),
        (
            DiaryEntry.dominant_emotion_label.in_(NEGATIVE_EMOTIONS),
            -1,
        ),
        else_=0,
    )

    avg_score = (
        db.session.query(func.avg(score_expr).label("avg_idx"))
        .filter(
            DiaryEntry.owner_id == current_user.id,
            DiaryEntry.dominant_emotion_label.isnot(None),
            DiaryEntry.created_at.between(start_date, end_date),
        )
        .scalar()
    )

    response = {
        "start": start_date.date().isoformat(),
        "end": end_date.date().isoformat(),
        "average_mood_index": round(avg_score or 0, 2),
    }
    return jsonify(response)
