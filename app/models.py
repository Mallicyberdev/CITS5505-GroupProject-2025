from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import func
from .extensions import db, login_manager

# association table for shared diaries
diary_shares = db.Table(
    'diary_shares',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('diary_id', db.Integer, db.ForeignKey('diary_entries.id'), primary_key=True),
    db.Column('shared_at', db.DateTime, server_default=func.now())
)


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True, unique=True, nullable=False)
    email = db.Column(db.String(32), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    diaries = db.relationship(
        'DiaryEntry',
        backref='owner',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    shared_diaries = db.relationship(
        'DiaryEntry',
        secondary=diary_shares,
        backref=db.backref('shared_with', lazy='dynamic'),
        lazy='dynamic'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username!r}>'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class DiaryEntry(db.Model):
    __tablename__ = 'diary_entries'

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)

    created_at = db.Column(
        db.DateTime,
        server_default=func.now(),
        index=True
    )
    updated_at = db.Column(
        db.DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    # --- Emotion Analysis Fields ---

    # Store the label of the dominant (highest score) emotion
    dominant_emotion_label = db.Column(db.String(64), nullable=True, index=True)

    # Store the score of the dominant emotion
    dominant_emotion_score = db.Column(db.Float, nullable=True, index=True)

    # Store the full list of emotion labels and scores as JSON
    # Use SQLAlchemy's JSON type, which handles backend differences (including SQLite)
    emotion_details_json = db.Column(db.JSON, nullable=True)

    # Flag to indicate if analysis has been performed
    analyzed = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=func.false(),
        index=True
    )

    def __repr__(self):
        return f'<DiaryEntry {self.id} owner={self.owner.username!r}>'

    # --- Helper Method to Update Emotion Data ---
    def update_emotion_analysis(self, analysis_result):
        """
        Updates the diary entry with emotion analysis results.

        Args:
            analysis_result: The raw result from your analysis, expected to be
                             like [[{'label': 'anger', 'score': 0.01}, ...]]
        """
        if not analysis_result or not isinstance(analysis_result, list) or not analysis_result[0]:
            # Handle empty or invalid results
            self.dominant_emotion_label = None
            self.dominant_emotion_score = None
            self.emotion_details_json = None
            self.analyzed = True  # Mark as analyzed, even if result was empty/invalid
            return

        # --- IMPORTANT: Handle the nested list structure ---
        # Your input is [[{...}, {...}]], we need the inner list [{...}, {...}]
        emotion_scores = analysis_result[0]  # Get the actual list of scores

        if not emotion_scores:
            # Handle empty inner list
            self.dominant_emotion_label = None
            self.dominant_emotion_score = None
            self.emotion_details_json = None
            self.analyzed = True
            return

        # Find dominant emotion
        dominant_emotion = max(emotion_scores, key=lambda item: item['score'])

        # Update fields
        self.dominant_emotion_label = dominant_emotion['label']
        self.dominant_emotion_score = dominant_emotion['score']
        self.emotion_details_json = emotion_scores  # Store the list of dicts
        self.analyzed = True
