# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"  # The endpoint name for the login view
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"  # Bootstrap alert category
