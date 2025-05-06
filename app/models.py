from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

from .extensions import db, login_manager

diary_shares = db.Table(
    "diary_shares",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("diary_id", db.Integer, db.ForeignKey("diary_entry.id"), primary_key=True),
    db.Column("shared_at", db.DateTime, default=datetime.utcnow, nullable=False),
)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    _password = db.Column("password_hash", db.String(256), nullable=False)

    diaries = db.relationship(
        "DiaryEntry", back_populates="owner", cascade="all, delete-orphan"
    )
    shared_diaries = db.relationship(
        "DiaryEntry",
        secondary=diary_shares,
        back_populates="shared_with",
        lazy="dynamic",
    )

    @property
    def password(self):
        raise AttributeError("Password is write‑only")

    @password.setter
    def password(self, plain_password):
        self._password = generate_password_hash(plain_password)

    def verify_password(self, plain_password):
        return check_password_hash(self._password, plain_password)

    def __repr__(self):
        return f"<User {self.username!r}>"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class DiaryEntry(db.Model):
    __tablename__ = "diary_entry"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    owner = db.relationship("User", back_populates="diaries")

    title = db.Column(db.String(140), nullable=False)
    content = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    sentiment_score = db.Column(db.Float)
    sentiment_label = db.Column(db.String(32))
    sentiment_data = db.Column(db.JSON)

    dominant_emotion_label = db.Column(db.String(64), index=True)
    dominant_emotion_score = db.Column(db.Float, index=True)
    emotion_details_json = db.Column(db.JSON)
    analyzed = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=func.false(),
        index=True,
    )

    shared_with = db.relationship(
        "User",
        secondary=diary_shares,
        back_populates="shared_diaries",
        lazy="dynamic",
    )

    def is_shared(self, user):
        return (
            self.owner_id != user.id
            and self.shared_with.filter_by(id=user.id).count() > 0
        )

    def share_to(self, user):
        if not self.is_shared(user):
            self.shared_with.append(user)

    def unshare_from(self, user):
        self.shared_with.remove(user)

    def update_emotion_analysis(self, analysis_result):
        if (
            not analysis_result
            or not isinstance(analysis_result, list)
            or not analysis_result[0]
        ):
            self.dominant_emotion_label = None
            self.dominant_emotion_score = None
            self.emotion_details_json = None
            self.analyzed = True
            return

        emotion_scores = analysis_result[0]
        dominant = max(emotion_scores, key=lambda item: item["score"])
        self.dominant_emotion_label = dominant["label"]
        self.dominant_emotion_score = dominant["score"]
        self.emotion_details_json = emotion_scores
        self.analyzed = True

    def __repr__(self):
        return f"<DiaryEntry {self.id} {self.title!r}>"
