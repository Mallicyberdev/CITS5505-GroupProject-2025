import pytest
from flask import url_for
from app import create_app, db
from app.models import User, DiaryEntry
from unittest.mock import patch

@pytest.fixture
def app():
    """Create a test Flask app with an in-memory database."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False  # Disable CSRF for testing
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client for the Flask app."""
    return app.test_client()

@pytest.fixture
def user(app):
    """Create a test user and return its ID."""
    with app.app_context():
        user = User(username="testuser", email="test@example.com")
        user.set_password("testpassword")
        db.session.add(user)
        db.session.commit()
        yield user.id  # Yield the user ID instead of the user object
        db.session.delete(User.query.get(user.id))
        db.session.commit()

@pytest.fixture
def logged_in_client(client, user, app):
    """Log in a test user and return the client."""
    with app.app_context():
        client.post("/auth/login", data={
            "username": "testuser",
            "password": "testpassword",
            "remember_me": False
        }, follow_redirects=True)
        yield client

def test_register_success(client, app):
    """Test successful user registration."""
    response = client.post("/auth/register", data={
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "password123",
        "password2": "password123"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Congratulations, you are now a registered user!" in response.data
    with app.app_context():
        user = db.session.query(User).filter_by(username="newuser").first()
        assert user is not None
        assert user.email == "newuser@example.com"

def test_register_duplicate_username(client, user, app):
    """Test registration with duplicate username."""
    response = client.post("/auth/register", data={
        "username": "testuser",
        "email": "newemail@example.com",
        "password": "password123",
        "password2": "password123"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Please use a different username." in response.data

def test_login_success(client, user, app):
    """Test successful login."""
    response = client.post("/auth/login", data={
        "username": "testuser",
        "password": "testpassword"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome back, testuser!" in response.data

def test_login_invalid_credentials(client, user, app):
    """Test login with invalid credentials."""
    response = client.post("/auth/login", data={
        "username": "testuser",
        "password": "wrongpassword"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data

def test_logout(logged_in_client):
    """Test logout functionality."""
    response = logged_in_client.get("/auth/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"You have been logged out." in response.data

def test_create_diary(logged_in_client, user, app):
    """Test creating a diary entry."""
    with patch("app.data_handling.routes.emotion_classifier") as mock_classifier:
        mock_classifier.return_value = [[
            {"label": "happy", "score": 0.9},
            {"label": "sad", "score": 0.1}
        ]]
        response = logged_in_client.post("/data/create_diary", data={
            "title": "Test Diary",
            "content": "This is a happy day!"
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"Diary created successfully!" in response.data
        with app.app_context():
            diary = db.session.query(DiaryEntry).filter_by(title="Test Diary").first()
            assert diary is not None
            assert diary.content == "This is a happy day!"
            assert diary.dominant_emotion_label == "happy"
            assert diary.dominant_emotion_score == 0.9
            assert diary.emotion_details_json == [
                {"label": "happy", "score": 0.9},
                {"label": "sad", "score": 0.1}
            ]

def test_edit_diary(logged_in_client, user, app):
    """Test editing a diary entry."""
    with app.app_context():
        diary = DiaryEntry(title="Original", content="Original content", owner_id=user)
        db.session.add(diary)
        db.session.commit()
        diary_id = diary.id
    with patch("app.data_handling.routes.emotion_classifier") as mock_classifier:
        mock_classifier.return_value = [[
            {"label": "sad", "score": 0.8},
            {"label": "happy", "score": 0.2}
        ]]
        response = logged_in_client.post(f"/data/edit_diary/{diary_id}", data={
            "title": "Updated Diary",
            "content": "This is a sad day."
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"Diary entry updated successfully!" in response.data
        with app.app_context():
            diary = db.session.get(DiaryEntry, diary_id)
            assert diary.title == "Updated Diary"
            assert diary.content == "This is a sad day."
            assert diary.dominant_emotion_label == "sad"
            assert diary.dominant_emotion_score == 0.8

def test_view_diary(logged_in_client, user, app):
    """Test viewing a diary entry."""
    with app.app_context():
        diary = DiaryEntry(title="Test Diary", content="View this diary", owner_id=user)
        db.session.add(diary)
        db.session.commit()
        diary_id = diary.id
    response = logged_in_client.get(f"/data/view_diary/{diary_id}")
    assert response.status_code == 200
    assert b"Test Diary" in response.data
    assert b"View this diary" in response.data

def test_delete_diary(logged_in_client, user, app):
    """Test deleting a diary entry."""
    with app.app_context():
        diary = DiaryEntry(title="To Delete", content="Delete this", owner_id=user)
        db.session.add(diary)
        db.session.commit()
        diary_id = diary.id
    response = logged_in_client.post(f"/data/delete_diary/{diary_id}", follow_redirects=True)
    assert response.status_code == 200
    assert b"Diary entry deleted successfully." in response.data
    with app.app_context():
        diary = db.session.get(DiaryEntry, diary_id)
        assert diary is None

def test_share_diary(logged_in_client, user, app):
    """Test sharing a diary entry with another user."""
    with app.app_context():
        other_user = User(username="otheruser", email="other@example.com")
        other_user.set_password("otherpassword")
        db.session.add(other_user)
        diary = DiaryEntry(title="Shared Diary", content="Share this", owner_id=user)
        db.session.add(diary)
        db.session.commit()
        diary_id = diary.id
    response = logged_in_client.post(f"/data/share_diary/{diary_id}", data={
        "shared_users": ["otheruser"]
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Diary sharing updated" in response.data
    with app.app_context():
        diary = db.session.get(DiaryEntry, diary_id)
        shared_users = diary.get_shared_users()
        assert len(shared_users) == 1
        assert shared_users[0].username == "otheruser"

def test_unshare_diary(logged_in_client, user, app):
    """Test unsharing a diary entry."""
    with app.app_context():
        other_user = User(username="otheruser", email="other@example.com")
        other_user.set_password("otherpassword")
        db.session.add(other_user)
        diary = DiaryEntry(title="Shared Diary", content="Share this", owner_id=user)
        diary.shared_with.append(other_user)
        db.session.add(diary)
        db.session.commit()
        diary_id = diary.id
    response = logged_in_client.post(f"/data/share_diary/{diary_id}", data={
        "shared_users": []
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Diary sharing updated" in response.data
    with app.app_context():
        diary = db.session.get(DiaryEntry, diary_id)
        shared_users = diary.get_shared_users()
        assert len(shared_users) == 0

def test_unauthorized_access(logged_in_client, user, app):
    """Test accessing a diary entry without permission."""
    with app.app_context():
        other_user = User(username="otheruser", email="other@example.com")
        other_user.set_password("otherpassword")
        db.session.add(other_user)
        db.session.commit()
        other_user_id = other_user.id
        diary = DiaryEntry(title="Private Diary", content="Private", owner_id=other_user_id)
        db.session.add(diary)
        db.session.commit()
        diary_id = diary.id
    response = logged_in_client.get(f"/data/view_diary/{diary_id}", follow_redirects=True)
    assert response.status_code == 200
    assert b"You do not have permission to view this diary entry." in response.data
