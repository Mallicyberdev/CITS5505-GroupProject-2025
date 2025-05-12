# routes.py
from flask import request, render_template, flash, url_for, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import redirect

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


@bp.route("/create_diary", methods=["GET", "POST"])
@login_required
def create_diary():
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
            flash(f"Diary sharing updated (changes applied to {success_count} user(s)).", "success")
        else:
            flash("No changes made to sharing settings.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to update diary sharing: {str(e)}", "danger")

    return redirect(url_for("data_handling.view_diary", diary_id=diary_id))


@bp.route("/list_users", methods=["GET"])
@login_required
def list_users():
    users = User.query.all()
    return jsonify([{"id": user.id, "username": user.username} for user in users])


@bp.route("/get_shared_users/<int:diary_id>", methods=["GET"])
@login_required
def get_shared_users(diary_id):
    diary_entry = DiaryEntry.query.get_or_404(diary_id)
    if diary_entry.owner_id != current_user.id:
        flash("You can only view shared users for diaries you own.", "danger")
        return jsonify([]), 403
    shared_users = diary_entry.get_shared_users()
    return jsonify([{"id": user.id, "username": user.username} for user in shared_users])