"""
Flask application entry point for US Economic Pulse.
Replaces proxy.py — adds authentication and serves the dashboard.
"""
import os
import urllib.request

from flask import Flask, send_from_directory, request, Response
from flask_login import LoginManager, login_required

import db
from models import User

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = Flask(__name__, template_folder="templates")
app.secret_key = os.environ["SECRET_KEY"]

# ---------------------------------------------------------------------------
# Flask-Login setup
# ---------------------------------------------------------------------------

login_manager = LoginManager(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access the dashboard."
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    row = db.get_user_by_id(int(user_id))
    if row is None:
        return None
    return User(row)


# ---------------------------------------------------------------------------
# Blueprints — imported after app + login_manager are defined
# ---------------------------------------------------------------------------

from auth import auth_bp   # noqa: E402
from admin import admin_bp  # noqa: E402

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)

# ---------------------------------------------------------------------------
# Dashboard (protected)
# ---------------------------------------------------------------------------

FRED_API = "https://api.stlouisfed.org/fred/series/observations"


@app.route("/")
@login_required
def index():
    return send_from_directory(".", "index.html")


@app.route("/fred")
@login_required
def fred_proxy():
    """Proxy /fred?... → FRED API, forwarding all query parameters."""
    qs = request.query_string.decode()
    target = f"{FRED_API}?{qs}" if qs else FRED_API
    try:
        req = urllib.request.Request(target, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read()
        return Response(body, status=200, mimetype="application/json")
    except Exception as exc:
        return Response(str(exc), status=502, mimetype="text/plain")


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    db.init_db()
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting US Economic Pulse on port {port}")
    app.run(host="0.0.0.0", port=port)
