"""
Application factory module of the Mood Diary Analysis app.

Initializes the Flask app and its extensions,
configures the database, and mounts blueprints.
"""

import os
from flask import Flask
from .extensions import db, migrate, login_manager
from config import Config

def create_app(config_class=Config):
    """Create and configure the Flask application.

        Args:
           config_class: Class to use for configuration (default: Config)

        Returns:
           Flask: Configured Flask application instance
    """
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration from config.py
    app.config.from_object(config_class)

    # Load configuration from instance/config.py if it exists
    # Use silent=True to not raise an error if the file doesn't exist
    app.config.from_pyfile("config.py", silent=True)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass  # Already exists

    # Initialize Flask extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Create database tables if they don't exist (since not using Migrate)
    with app.app_context():
        # Import models here to ensure they are known to SQLAlchemy
        from . import models

        db.create_all()
        print(f"Database checked/created at {app.config['SQLALCHEMY_DATABASE_URI']}")

    # Register Blueprints
    from .main import bp as main_bp

    app.register_blueprint(main_bp)

    from .auth import bp as auth_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")

    from .data_handling import bp as data_handling_bp

    app.register_blueprint(data_handling_bp, url_prefix="/data")

    return app
