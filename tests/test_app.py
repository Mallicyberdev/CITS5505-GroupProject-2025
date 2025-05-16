import unittest
from unittest.mock import patch
from flask import url_for, get_flashed_messages
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import User, DiaryEntry
from app.auth.forms import LoginForm, RegistrationForm
from app.data_handling.forms import DiaryForm

class TestConfig:
    """Test configuration for in-memory SQLite database."""
    SECRET_KEY = 'test-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    WTF_CSRF_ENABLED = False  # Disable CSRF for easier testing

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the test environment."""
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        """Tear down the test environment."""
        db.session.close()  # Close the session
        db.drop_all()
        db.engine.dispose()  # Dispose of the engine to close connections
        self.app_context.pop()

    def login(self, username, password):
        """Helper method to log in a user."""
        return self.client.post('/auth/login', data={
            'username': username,
            'password': password,
            'remember_me': True
        }, follow_redirects=True)

class AuthTests(BaseTestCase):
    def test_user_model(self):
        """Test User model functionality."""
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        # Verify user creation
        saved_user = User.query.filter_by(username='testuser').first()
        self.assertIsNotNone(saved_user)
        self.assertEqual(saved_user.email, 'test@example.com')
        self.assertTrue(saved_user.check_password('password123'))
        self.assertFalse(saved_user.check_password('wrongpassword'))

    def test_login_form_validation(self):
        """Test LoginForm validation."""
        form = LoginForm(data={'username': 'testuser', 'password': 'password123', 'remember_me': True})
        self.assertTrue(form.validate())

        # Test missing data
        form = LoginForm(data={'username': '', 'password': 'password123'})
        self.assertFalse(form.validate())
        self.assertIn('This field is required.', form.username.errors)

    def test_registration_form_validation(self):
        """Test RegistrationForm validation."""
        form = RegistrationForm(
            data={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'password123',
                'password2': 'password123'
            }
        )
        self.assertTrue(form.validate())

        # Test password mismatch
        form = RegistrationForm(
            data={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'password123',
                'password2': 'different'
            }
        )
        self.assertFalse(form.validate())
        self.assertIn('Passwords must match.', form.password2.errors)

        # Test duplicate username
        user = User(username='testuser', email='other@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        form = RegistrationForm(
            data={
                'username': 'testuser',
                'email': 'new@example.com',
                'password': 'password123',
                'password2': 'password123'
            }
        )
        self.assertFalse(form.validate())
        self.assertIn('Please use a different username.', form.username.errors)

    def test_login_route(self):
        """Test the login route."""
        # Create a test user
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        # Test successful login
        with self.client:
            response = self.login('testuser', 'password123')
            self.assertEqual(response.status_code, 200)
            messages = get_flashed_messages()
            self.assertIn('Welcome back, testuser!', messages)
            # Log out to clear session
            self.client.get('/auth/logout', follow_redirects=True)

        # Test invalid credentials
        with self.client:
            response = self.client.post('/auth/login', data={
                'username': 'testuser',
                'password': 'wrongpassword'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Log In', response.data)  # Verify login page
            self.assertIn(b'Invalid username or password', response.data)

    def test_logout_route(self):
        """Test the logout route."""
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        with self.client:
            self.login('testuser', 'password123')
            response = self.client.get('/auth/logout', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            messages = get_flashed_messages()
            self.assertIn('You have been logged out.', messages)

    def test_register_route(self):
        """Test the register route."""
        with self.client:
            response = self.client.post('/auth/register', data={
                'username': 'newuser',
                'email': 'new@example.com',
                'password': 'password123',
                'password2': 'password123'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            messages = get_flashed_messages()
            self.assertIn('Congratulations, you are now a registered user!', messages)

            # Verify user was created
            user = User.query.filter_by(username='newuser').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.email, 'new@example.com')

class DiaryTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        # Create a test user
        self.user = User(username='testuser', email='test@example.com')
        self.user.set_password('password123')
        db.session.add(self.user)
        db.session.commit()

    @patch('app.data_handling.routes.emotion_classifier')
    def test_diary_creation(self, mock_classifier):
        """Test diary creation with mocked emotion classifier."""
        # Mock emotion classifier response
        mock_classifier.return_value = [[
            {'label': 'happy', 'score': 0.9},
            {'label': 'sad', 'score': 0.05}
        ]]

        with self.client:
            self.login('testuser', 'password123')
            response = self.client.post('/data/create_diary', data={
                'title': 'Test Diary',
                'content': 'This is a test diary entry.'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            messages = get_flashed_messages()
            self.assertIn('Diary created and analyzed successfully!', messages)

            # Verify diary entry
            diary = DiaryEntry.query.filter_by(title='Test Diary').first()
            self.assertIsNotNone(diary)
            self.assertEqual(diary.content, 'This is a test diary entry.')
            self.assertEqual(diary.dominant_emotion_label, 'happy')
            self.assertEqual(diary.dominant_emotion_score, 0.9)
            self.assertTrue(diary.analyzed)

    @patch('app.data_handling.routes.emotion_classifier')
    def test_diary_edit(self, mock_classifier):
        """Test diary editing with mocked emotion classifier."""
        # Create a diary entry
        diary = DiaryEntry(title='Original', content='Original content', owner_id=self.user.id)
        mock_classifier.return_value = [[
            {'label': 'neutral', 'score': 0.8},
            {'label': 'happy', 'score': 0.1}
        ]]
        diary.update_emotion_analysis(mock_classifier.return_value)
        db.session.add(diary)
        db.session.commit()

        # Update diary
        mock_classifier.return_value = [[
            {'label': 'sad', 'score': 0.7},
            {'label': 'neutral', 'score': 0.2}
        ]]
        with self.client:
            self.login('testuser', 'password123')
            response = self.client.post(f'/data/edit_diary/{diary.id}', data={
                'title': 'Updated Diary',
                'content': 'Updated content'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            messages = get_flashed_messages()
            self.assertIn('Diary entry updated successfully!', messages)

            # Verify updates
            updated_diary = db.session.get(DiaryEntry, diary.id)
            self.assertEqual(updated_diary.title, 'Updated Diary')
            self.assertEqual(updated_diary.content, 'Updated content')
            self.assertEqual(updated_diary.dominant_emotion_label, 'sad')
            self.assertEqual(updated_diary.dominant_emotion_score, 0.7)

    def test_diary_delete(self):
        """Test diary deletion."""
        diary = DiaryEntry(title='To Delete', content='Content', owner_id=self.user.id)
        db.session.add(diary)
        db.session.commit()

        with self.client:
            self.login('testuser', 'password123')
            response = self.client.post(f'/data/delete_diary/{diary.id}', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            messages = get_flashed_messages()
            self.assertIn('Diary entry deleted successfully.', messages)

            # Verify deletion
            self.assertIsNone(db.session.get(DiaryEntry, diary.id))

    def test_diary_share(self):
        """Test diary sharing functionality."""
        # Create another user
        user2 = User(username='user2', email='user2@example.com')
        user2.set_password('password123')
        db.session.add(user2)
        db.session.commit()

        # Create a diary entry
        diary = DiaryEntry(title='Shared Diary', content='Content', owner_id=self.user.id)
        db.session.add(diary)
        db.session.commit()

        with self.client:
            self.login('testuser', 'password123')
            response = self.client.post(f'/data/share_diary/{diary.id}', data={
                'shared_users': ['user2']
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            messages = get_flashed_messages()
            self.assertIn('Diary sharing updated successfully! 1 changes made.', messages)

            # Verify sharing
            self.assertTrue(diary.is_shared_with_user(user2))

    def test_diary_access_control(self):
        """Test access control for diary viewing."""
        # Create another user
        user2 = User(username='user2', email='user2@example.com')
        user2.set_password('password123')
        db.session.add(user2)
        db.session.commit()

        # Create a diary entry
        diary = DiaryEntry(title='Private Diary', content='Content', owner_id=self.user.id)
        db.session.add(diary)
        db.session.commit()

        # Test unauthorized access
        with self.client:
            self.login('user2', 'password123')
            response = self.client.get(f'/data/view_diary/{diary.id}', follow_redirects=True)
            messages = get_flashed_messages()
            self.assertIn('You do not have permission to view this diary entry.', messages)

            # Share diary with user2
            self.login('testuser', 'password123')
            diary.share_with_user(user2)
            db.session.commit()

            # Test authorized access
            self.login('user2', 'password123')
            response = self.client.get(f'/data/view_diary/{diary.id}', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Private Diary', response.data)

if __name__ == '__main__':
    unittest.main()