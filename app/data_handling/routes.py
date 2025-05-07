from flask import request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.exceptions import RequestEntityTooLarge

from . import bp
from app import db
from app.models import DiaryEntry

@bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    try:
        # Get form data instead of files
        title = request.form.get('title')
        content = request.form.get('content')

        if not title or not content:
            flash('Title and content are required', 'error')
            return redirect(url_for('main.upload_diary'))

        # Create diary entry from form data
        diary_entry = DiaryEntry(
            owner_id=current_user.id,
            title=title,
            content=content
        )
        
        db.session.add(diary_entry)
        db.session.commit()

        flash('Diary entry created successfully!', 'success')
        return redirect(url_for('main.dashboard'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error creating diary entry: {str(e)}', 'error')
        return redirect(url_for('main.upload_diary'))