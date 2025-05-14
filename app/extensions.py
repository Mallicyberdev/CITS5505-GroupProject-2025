# app/extensions.py
"""
Flask extensions initialization.

This module initializes Flask extensions used throughout the application
and configures their default settings.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate(db)
login_manager = LoginManager()
login_manager.login_view = "auth.login"  # The endpoint name for the login view
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"  # Bootstrap alert category
