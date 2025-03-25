from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User
from app import db

auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # Validation
        if not username or not email or not password:
            flash("All fields are required")
            return redirect(url_for("auth.register"))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists")
            return redirect(url_for("auth.register"))

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash("Email already registered")
            return redirect(url_for("auth.register"))

        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please log in.")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash("Please check your login details and try again.")
            return redirect(url_for("auth.login"))

        session["user_id"] = user.id
        return redirect(url_for("dashboard.index"))

    return render_template("login.html")


@auth.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("You have been logged out.")
    return redirect(url_for("auth.login"))
