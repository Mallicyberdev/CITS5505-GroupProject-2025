# app/auth/forms.py
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
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")

class RegistrationForm(FlaskForm):
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