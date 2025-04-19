# config.py
import os

# Find the absolute path of the directory containing config.py
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Use instance folder for the database if it exists, otherwise use the base directory
    instance_path = os.path.join(basedir, "instance")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(
        instance_path if os.path.exists(instance_path) else basedir, "app.db"
    )
