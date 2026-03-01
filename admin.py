"""
Admin blueprint: user approval/rejection panel.
All routes require the current user to be authenticated AND is_admin=True.
"""
import functools

from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

import db
import email_utils

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    """Decorator: 403 unless the logged-in user is an admin."""
    @functools.wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin_user:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/users")
@admin_required
def users():
    pending = db.get_pending_users()
    return render_template("admin/users.html", pending=pending)


@admin_bp.route("/approve/<int:user_id>", methods=["POST"])
@admin_required
def approve(user_id):
    row = db.get_user_by_id(user_id)
    if row is None:
        abort(404)
    db.approve_user(user_id)
    email_utils.send_approval_email(row["username"], row["email"])
    flash(f"Approved {row['username']}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/reject/<int:user_id>", methods=["POST"])
@admin_required
def reject(user_id):
    row = db.get_user_by_id(user_id)
    if row is None:
        abort(404)
    db.reject_user(user_id)
    flash(f"Rejected and removed {row['username']}.", "success")
    return redirect(url_for("admin.users"))
