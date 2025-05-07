from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import func, or_
from .extensions import db, login_manager

# association table for shared diaries
diary_shares = db.Table(
    "diary_shares",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column(
        "diary_id", db.Integer, db.ForeignKey("diary_entries.id"), primary_key=True
    ),
    db.Column("shared_at", db.DateTime, server_default=func.now()),
)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True, unique=True, nullable=False)
    email = db.Column(db.String(32), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    diaries = db.relationship(
        "DiaryEntry", backref="owner", lazy="dynamic", cascade="all, delete-orphan"
    )
    shared_diaries = db.relationship(
        "DiaryEntry",
        secondary=diary_shares,
        backref=db.backref("shared_with", lazy="dynamic"),
        lazy="dynamic",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username!r}>"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class DiaryEntry(db.Model):
    __tablename__ = "diary_entries"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, server_default=func.now(), index=True)
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

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
        index=True,
    )

    def __repr__(self):
        return f"<DiaryEntry {self.id} owner={self.owner.username!r}>"

    # --- Helper Method to Update Emotion Data ---
    def update_emotion_analysis(self, analysis_result):
        """
        Updates the diary entry with emotion analysis results.

        Args:
            analysis_result: The raw result from your analysis, expected to be
                             like [[{'label': 'anger', 'score': 0.01}, ...]]
        """
        if (
            not analysis_result
            or not isinstance(analysis_result, list)
            or not analysis_result[0]
        ):
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
        dominant_emotion = max(emotion_scores, key=lambda item: item["score"])

        # Update fields
        self.dominant_emotion_label = dominant_emotion["label"]
        self.dominant_emotion_score = dominant_emotion["score"]
        self.emotion_details_json = emotion_scores  # Store the list of dicts
        self.analyzed = True

    @classmethod
    def for_user(cls, user_id):
        return cls.query.filter(
            or_(cls.owner_id == user_id, cls.shared_with.any(id=user_id))
        ).order_by(cls.created_at.desc())

    # --- Methods for Managing Diary Sharing ---

    def is_shared_with_user(self, user_to_check: User) -> bool:
        """
        Checks if this diary entry is currently shared with the given user.
        Note: `self.shared_with` is a dynamic query.
        """
        if not isinstance(user_to_check, User):
            raise TypeError("Expected a User object for user_to_check.")
        # owner cannot be in shared_with list
        if self.owner_id == user_to_check.id:
            return False
        return self.shared_with.filter(User.id == user_to_check.id).first() is not None

    def share_with_user(self, user_to_share: User) -> bool:
        """
        Shares this diary entry with the given user.
        Returns True if successfully shared, False if already shared or user is owner.
        """
        if not isinstance(user_to_share, User):
            raise TypeError("Expected a User object for user_to_share.")

        # Prevent sharing with the owner through the sharing mechanism
        if self.owner_id == user_to_share.id:
            # print(f"Cannot share diary {self.id} with its owner {user_to_share.username}")
            return False

        if not self.is_shared_with_user(user_to_share):
            self.shared_with.append(user_to_share)
            # db.session.add(self) # Not strictly necessary if self is already managed by session
            # db.session.commit() # Commit should be handled by the caller/route
            return True
        # print(f"Diary {self.id} is already shared with user {user_to_share.username}")
        return False  # Already shared or attempted to share with owner

    def unshare_from_user(self, user_to_unshare: User) -> bool:
        """
        Unshares this diary entry from the given user.
        Returns True if successfully unshared, False if not shared with this user.
        """
        if not isinstance(user_to_unshare, User):
            raise TypeError("Expected a User object for user_to_unshare.")

        # Owner cannot be "unshared" from their own diary via this mechanism
        if self.owner_id == user_to_unshare.id:
            return False

        if self.is_shared_with_user(user_to_unshare):
            self.shared_with.remove(user_to_unshare)
            # db.session.add(self)
            # db.session.commit()
            return True
        return False  # Was not shared with this user

    def get_shared_users(self) -> list[User]:
        """
        Returns a list of User objects with whom this diary entry is shared.
        """
        return self.shared_with.all()
