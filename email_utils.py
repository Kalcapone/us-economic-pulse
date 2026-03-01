"""
SMTP email helpers for registration notifications and approval emails.
Failures are logged but never crash the app.
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def _send(to_addr: str, subject: str, body: str) -> None:
    """Internal: send a plain-text email via STARTTLS SMTP."""
    host = os.environ.get("SMTP_HOST", "")
    port = int(os.environ.get("SMTP_PORT", 587))
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASS", "")
    from_addr = os.environ.get("SMTP_FROM", user)

    if not host or not user:
        logger.warning("SMTP not configured — skipping email to %s", to_addr)
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr

    try:
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(user, password)
            smtp.sendmail(from_addr, [to_addr], msg.as_string())
        logger.info("Email sent to %s: %s", to_addr, subject)
    except Exception:
        logger.exception("Failed to send email to %s", to_addr)


def send_admin_notification(username: str, email: str) -> None:
    """Notify the admin that a new user has registered and needs approval."""
    admin_email = os.environ.get("ADMIN_EMAIL", "")
    if not admin_email:
        logger.warning("ADMIN_EMAIL not set — skipping admin notification")
        return

    app_url = os.environ.get("APP_URL", "").rstrip("/")
    approve_url = f"{app_url}/admin/users" if app_url else "/admin/users"

    subject = f"[US Economic Pulse] New registration: {username}"
    body = (
        f"A new user has registered and is awaiting your approval.\n\n"
        f"  Username : {username}\n"
        f"  Email    : {email}\n\n"
        f"Review and approve at:\n  {approve_url}\n"
    )
    _send(admin_email, subject, body)


def send_approval_email(username: str, email: str) -> None:
    """Notify the user that their account has been approved."""
    app_url = os.environ.get("APP_URL", "").rstrip("/")
    login_url = f"{app_url}/login" if app_url else "/login"

    subject = "[US Economic Pulse] Your account has been approved"
    body = (
        f"Hi {username},\n\n"
        f"Your account has been approved. You can now log in at:\n  {login_url}\n\n"
        f"Welcome to US Economic Pulse!\n"
    )
    _send(email, subject, body)
