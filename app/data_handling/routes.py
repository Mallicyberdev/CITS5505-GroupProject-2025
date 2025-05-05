# routes.py

from pathlib import Path
import tempfile

from flask import request, jsonify
from flask_login import login_required, current_user
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from . import bp
from app import db
from app.models import DiaryEntry
from .utils import validate_file

ALLOWED_EXTENSIONS = {'txt', 'json', 'csv'}
UPLOAD_PROGRESS = {}               # TODO: 

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/upload/progress/<upload_id>')
@login_required
def upload_progress(upload_id):
    return jsonify(UPLOAD_PROGRESS.get(upload_id, {}))


@bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    upload_id = None         
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({'error': 'No selected file'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400

        # validate_file() — ваша доп.‑проверка
        is_valid, message = validate_file(file)
        if not is_valid:
            return jsonify({'error': message}), 400

        filename = secure_filename(file.filename)
        upload_id = f"{current_user.id}_{filename}"
        UPLOAD_PROGRESS[upload_id] = {'status': 'processing', 'progress': 0}

        
        total_size = request.content_length or 0          
        bytes_read = 0
        tmp_path = Path(tempfile.gettempdir()) / upload_id
        with tmp_path.open('wb') as tmp:
            for chunk in file.stream:                     
                tmp.write(chunk)
                bytes_read += len(chunk)
                if total_size:
                    progress = bytes_read / total_size * 100
                else:
                    progress = 0
                UPLOAD_PROGRESS[upload_id]['progress'] = progress

        
        
        with tmp_path.open('r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        diary_entry = DiaryEntry(
            owner_id=current_user.id,
            title=filename,
            content=content
        )
        db.session.add(diary_entry)
        db.session.commit()

        UPLOAD_PROGRESS[upload_id].update({'status': 'completed', 'progress': 100})
        return jsonify({'message': 'File uploaded', 'entry_id': diary_entry.id,
                        'upload_id': upload_id}), 201

    except RequestEntityTooLarge:
        return jsonify({'error': 'File size exceeds limit'}), 413

    except Exception as e:
        db.session.rollback()
        if upload_id:
            UPLOAD_PROGRESS[upload_id] = {'status': 'error', 'error': str(e)}
        return jsonify({'error': str(e)}), 500

    finally:
        
        if upload_id and UPLOAD_PROGRESS.get(upload_id, {}).get('status') in {'completed', 'error'}:
            UPLOAD_PROGRESS.pop(upload_id, None)