# routes.py
from flask import request, render_template, flash, url_for
from flask_login import login_required, current_user
from werkzeug.utils import redirect

from app import db
from app.models import User, DiaryEntry
from . import bp
from .forms import DiaryForm


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
        db.session.add(new_diary)
        db.session.commit()
        flash("Diary entry created successfully!", "success")
        return redirect(url_for("main.home"))  # Or your main diary list page

    # For GET request, or if form validation fails on POST
    return render_template("upload.html", title="Create Diary Entry", form=form)


@bp.route("/view_diary/<diary_id>")
@login_required
def view_diary(diary_id):
    diary_entry = DiaryEntry.query.get_or_404(diary_id)
    if diary_entry.owner_id != current_user.id and not diary_entry.is_shared_with_user(
        current_user
    ):
        flash("You do not have permission to view this diary entry.", "danger")
        return redirect(url_for("main.home"))

    return render_template(
        "details.html", title="View Diary Entry", diary_entry=diary_entry
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
        diary_entry.content = form.content.data

        # Optional: Mark for re-analysis if content changed.
        # You might want a more sophisticated check if the content actually changed.
        # For simplicity, we can just mark it as not analyzed.
        diary_entry.analyzed = False
        diary_entry.dominant_emotion_label = None
        diary_entry.dominant_emotion_score = None
        diary_entry.emotion_details_json = None

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
    print(prev_url)
    # For GET request, or if form validation failed on POST, render the edit form
    return render_template(
        "edit.html",
        title="Edit Diary Entry",
        form=form,
        diary_entry=diary_entry,
        prev_url=prev_url,
    )


@bp.route(
    "/delete_diary/<int:diary_id>", methods=["POST"]
)  # Strictly POST for deletion
@login_required
def delete_diary(diary_id):
    diary_entry = db.session.get(DiaryEntry, diary_id)
    if not diary_entry:
        flash("Diary entry not found.", "warning")
        return redirect(url_for("main.home"))

    if diary_entry.owner_id != current_user.id:
        flash("You do not have permission to delete this diary entry.", "danger")
        # It might be better to redirect to the diary's view page if they somehow got here
        return redirect(url_for("data_handling.view_diary", diary_id=diary_id))

    # CSRF Protection: Flask-WTF handles CSRF if you're using a form for deletion
    # If you are not using a FlaskForm for the delete button in details.html,
    # you should implement CSRF protection manually or use a library like Flask-SeaSurf.
    # For simplicity, this example assumes the POST request is legitimate.
    # A common way is to create a simple DeleteForm(FlaskForm) with only a submit button
    # and validate it here, or check request.form.get('csrf_token').

    try:
        # Before deleting the diary, remove its shares if any.
        # SQLAlchemy should handle this automatically if the `diary_shares` table
        # has ON DELETE CASCADE for the `diary_id` foreign key,
        # or if the relationship is configured correctly.
        # If not, you might need to manually clear `diary_entry.shared_with`:
        # diary_entry.shared_with = []
        # db.session.commit() # Commit this change before deleting the diary object

        db.session.delete(diary_entry)
        db.session.commit()
        flash("Diary entry deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting diary entry: {str(e)}", "danger")
        # Log the error e for debugging

    return redirect(url_for("main.home"))  # Redirect to home page after deletion


@bp.route("/share_diary/<int:diary_id>", methods=["POST"])
@login_required
def share_diary(diary_id):
    diary_entry = DiaryEntry.query.get_or_404(diary_id)

    if diary_entry.owner_id != current_user.id:
        flash("You can only share diaries you own.", "danger")
        return redirect(url_for("main.home"))

    shared_username = request.form.get("shared_username")
    if not shared_username:
        flash("No username provided.", "warning")
        return redirect(url_for("data_handling.view_diary", diary_id=diary_id))

    shared_user = User.query.filter_by(username=shared_username).first()

    if not shared_user:
        flash("User not found.", "warning")
        return redirect(url_for("data_handling.view_diary", diary_id=diary_id))

    try:
        success = diary_entry.share_with_user(shared_user)
        if success:
            db.session.commit()
            flash(f"Diary shared with {shared_user.username}.", "success")
        else:
            flash(f"Diary already shared or cannot be shared with this user.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to share diary: {str(e)}", "danger")

    return redirect(url_for("data_handling.view_diary", diary_id=diary_id))
