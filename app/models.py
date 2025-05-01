# app/models.py
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db, login_manager   # db = SQLAlchemy(), login_manager = LoginManager()


########################################################################
#  Ассоциативная таблица «кому поделились дневником»
########################################################################
diary_shares = db.Table(
    "diary_shares",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"),  primary_key=True),
    db.Column("diary_id", db.Integer, db.ForeignKey("diary_entry.id"), primary_key=True),
    db.Column("shared_at", db.DateTime, default=datetime.utcnow, nullable=False)
)


########################################################################
#  Модель пользователя
########################################################################
class User(UserMixin, db.Model):
    __tablename__ = "user"

    id          = db.Column(db.Integer, primary_key=True)
    username    = db.Column(db.String(64), unique=True, nullable=False)
    email       = db.Column(db.String(120), unique=True, nullable=False)
    _password   = db.Column("password_hash", db.String(256), nullable=False)

    # ---- отношения ----------------------------------------------------
    diaries        = db.relationship(
        "DiaryEntry",
        back_populates="owner",
        cascade="all, delete-orphan"
    )
    shared_diaries = db.relationship(
        "DiaryEntry",
        secondary=diary_shares,
        back_populates="shared_with",
        lazy="dynamic"
    )

    # ---- методы безопасности -----------------------------------------
    @property
    def password(self):
        raise AttributeError("Password is write-only.")

    @password.setter
    def password(self, plain_password: str) -> None:
        self._password = generate_password_hash(plain_password)

    def verify_password(self, plain_password: str) -> bool:
        return check_password_hash(self._password, plain_password)

    # ---- полезное -----------------------------------------------------
    def __repr__(self) -> str:      # pragma: no cover
        return f"<User {self.username!r}>"


########################################################################
#  Модель дневника
########################################################################
class DiaryEntry(db.Model):
    __tablename__ = "diary_entry"

    id       = db.Column(db.Integer, primary_key=True)

    # владелец записи
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    owner    = db.relationship("User", back_populates="diaries")

    # основное содержимое
    title    = db.Column(db.String(140), nullable=False)
    content  = db.Column(db.Text, nullable=True)

    # даты
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # результаты анализа тональности (если используете NLP-пайплайн)
    sentiment_score = db.Column(db.Float,  nullable=True)
    sentiment_label = db.Column(db.String(32), nullable=True)         # e.g. "positive"
    sentiment_data  = db.Column(db.JSON,  nullable=True)              # raw model output

    # ---- с кем поделились --------------------------------------------
    shared_with = db.relationship(
        "User",
        secondary=diary_shares,
        back_populates="shared_diaries",
        lazy="dynamic"
    )

    # ---- удобство -----------------------------------------------------
    def is_shared(self, user: "User") -> bool:
        """Проверить, расшарена ли запись данному пользователю."""
        return self.owner_id != user.id and self.shared_with.filter_by(id=user.id).count() > 0

    def share_to(self, user: "User") -> None:
        """Поделиться записью с пользователем (если ещё не)."""
        if not self.is_shared(user):
            self.shared_with.append(user)          # flush позже в сервисе/view

    def unshare_from(self, user: "User") -> None:
        """Отозвать доступ у пользователя."""
        self.shared_with.remove(user)              # flush позже

    def __repr__(self) -> str:      # pragma: no cover
        return f"<DiaryEntry {self.id} {self.title!r}>"



#  Callback
@login_manager.user_loader
def load_user(user_id: int):
    return User.query.get(int(user_id))