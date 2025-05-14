"""
Form definitions for user authentication.

This module contains WTForms form classes for login, registration,
and other authentication-related functionality.

Classes:
    LoginForm: Handles user login form data and validation
    RegistrationForm: Handles new user registration form data and validation
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length

from app import db
from app.models import User
from sqlalchemy import select


class LoginForm(FlaskForm):
    """Form for user login.
    
    Fields:
        username (StringField): User's username
        password (PasswordField): User's password
        remember_me (BooleanField): Remember login session
        submit (SubmitField): Form submission button
    """
    
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class RegistrationForm(FlaskForm):
    """Form for new user registration.
    
    Fields:
        username (StringField): New user's username (3-64 chars)
        email (StringField): User's email address (max 120 chars)
        password (PasswordField): User's password (min 6 chars)
        password2 (PasswordField): Password confirmation
        submit (SubmitField): Form submission button

    Validators:
        - All fields are required
        - Username length: 3-64 characters
        - Email must be valid format and max 120 characters
        - Password minimum length: 6 characters
        - Passwords must match
    """
    
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=64)]
    )
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        "Repeat Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    submit = SubmitField("Register")

    def validate_username(self, username):
        """Validate username uniqueness."""
        user = db.session.scalar(select(User).filter_by(username=username.data))
        if user is not None:
            raise ValidationError("Please use a different username.")

    def validate_email(self, email):
        """Validate email uniqueness."""
        user = db.session.scalar(select(User).filter_by(email=email.data))
        if user is not None:
            raise ValidationError("Please use a different email address.")