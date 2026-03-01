"""
Authentication blueprint: /login, /register, /logout, /pending
"""
import bcrypt
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user

import db
from models import User
import email_utils

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        row = db.get_user_by_username(username)
        if row and bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
            if not row["is_approved"] and not row["is_admin"]:
                flash("Your account is awaiting admin approval.", "warning")
                return redirect(url_for("auth.login"))
            user = User(row)
            login_user(user)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("index"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        # --- validation ---
        error = None
        if not username or not email or not password:
            error = "All fields are required."
        elif len(username) < 3 or len(username) > 64:
            error = "Username must be between 3 and 64 characters."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif password != confirm:
            error = "Passwords do not match."
        elif db.get_user_by_username(username):
            error = "That username is already taken."

        if error:
            flash(error, "danger")
            return render_template("register.html")

        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        db.create_user(username, email, password_hash)
        email_utils.send_admin_notification(username, email)

        return redirect(url_for("auth.pending"))

    return render_template("register.html")


@auth_bp.route("/pending")
def pending():
    return render_template("pending.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
