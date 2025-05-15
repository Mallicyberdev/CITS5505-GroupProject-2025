# app/auth/routes.py
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required

from urllib.parse import urlparse
from app import db
from . import bp
from .forms import LoginForm, RegistrationForm
from app.models import User


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))  # Redirect logged-in users
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(
                "Invalid username or password", "danger"
            )  # Use Bootstrap category 'danger'
            return redirect(url_for("auth.login"))
        login_user(user, remember=form.remember_me.data)
        flash(f"Welcome back, {user.username}!", "success")

        # Redirect to the page user was trying to access, or index
        next_page = request.args.get("next")
        if not next_page or urlparse(next_page).netloc != "":
            next_page = url_for("main.index")
        return redirect(next_page)
    return render_template("auth/login.html", title="Sign In", form=form)


@bp.route("/logout")
@login_required  # Ensure user is logged in to log out
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Congratulations, you are now a registered user!", "success")
        # Log the user in automatically after registration
        login_user(user)
        return redirect(url_for("main.index"))
    return render_template("auth/register.html", title="Register", form=form)


@bp.route("/list_users", methods=["GET"])
@login_required
def list_users():
    users = User.query.all()
    return jsonify([{"id": user.id, "username": user.username} for user in users])
