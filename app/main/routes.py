
from datetime import datetime

from flask import render_template, request, jsonify
from flask_login import current_user, login_required
from sqlalchemy import select

from . import bp                        
from ..models import DiaryEntry, diary_shares, db   



@bp.route("/")
@bp.route("/index")
def index():
    
    return render_template("index.html")

@bp.route("/listdiaries", methods=["GET"])
@login_required
def list_diaries():
    

    
    owned_q = DiaryEntry.query.filter_by(owner_id=current_user.id)

    shared_q = (
        DiaryEntry.query
        .join(diary_shares, DiaryEntry.id == diary_shares.c.diary_id)
        .filter(diary_shares.c.user_id == current_user.id)
    )

    
    diaries_q = owned_q.union(shared_q).order_by(DiaryEntry.created_at.desc())

    wants_json = (
        request.accept_mimetypes.best == "application/json"
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
    )

    if wants_json:
        payload = [
            {
                "id": d.id,
                "title": d.title,
                "created_at": d.created_at.isoformat(),
                "updated_at": d.updated_at.isoformat(),
                "owner": d.owner.username,
                "shared": d.owner_id != current_user.id,
                "sentiment": {
                    "score": d.sentiment_score,
                    "label": d.sentiment_label,
                },
            }
            for d in diaries_q
        ]
        return jsonify(diaries=payload), 200


    diaries = diaries_q.all()
    return render_template("diary_list.html", diaries=diaries) #SSR can be changed