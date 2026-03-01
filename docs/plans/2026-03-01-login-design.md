# Login Page Implementation Plan — us-economic-pulse

## Context

The `us-economic-pulse` app (GitHub: `Kalcapone/us-economic-pulse`, hosted on Railway) is currently a completely open FRED economic data dashboard — no authentication, no user management. The entire app needs to be placed behind a login wall to restrict access. The goal is to add:
- Self-registration with admin approval (users sign up, admin approves before they can access the app)
- Email notifications to admin on new registrations and to users on approval
- A simple admin panel to approve/reject pending users
- PostgreSQL on Railway for user storage

**Chosen approach:** Flask + Flask-Login + PostgreSQL + bcrypt + smtplib

---

## Repo & Current State

- **Repo:** `https://github.com/Kalcapone/us-economic-pulse`
- **Current entry point:** `proxy.py` — stdlib-only Python HTTP server
  - Serves `index.html` (static dashboard)
  - Proxies `/fred?series_id=X` → `https://api.stlouisfed.org/fred/series/observations`
- **No existing auth, no database, no framework**
- **Deployment:** Railway via `Procfile: web: python3 proxy.py`
- **Key env var:** `FRED_API_KEY` (already set on Railway), `PORT`

---

## Architecture

### New files created
```
app.py          — Flask app factory + main entry (replaces proxy.py logic)
models.py       — User(UserMixin) wrapper to avoid circular imports
db.py           — PostgreSQL connection + user queries (psycopg2)
auth.py         — Blueprint: /login, /register, /logout, /pending routes
admin.py        — Blueprint: /admin/users, /admin/approve/<id>, /admin/reject/<id>
email_utils.py  — smtplib email helpers (send_admin_notification, send_approval_email)
templates/
  base.html     — Base template matching index.html dark aesthetic
  login.html    — Login form
  register.html — Registration form
  pending.html  — "Awaiting approval" page
  admin/
    users.html  — Admin user list with approve/reject buttons
```

### Files modified
```
requirements.txt — Added: flask, flask-login, psycopg2-binary, bcrypt
Procfile         — Changed to: web: python3 app.py
```

### Files untouched
```
proxy.py   — Kept for reference; replaced in practice by app.py
index.html — Still served by Flask (via send_from_directory), now behind @login_required
```

---

## Database Schema

```sql
CREATE TABLE users (
  id            SERIAL PRIMARY KEY,
  username      VARCHAR(64) UNIQUE NOT NULL,
  email         VARCHAR(120) UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  is_approved   BOOLEAN DEFAULT FALSE,
  is_admin      BOOLEAN DEFAULT FALSE,
  created_at    TIMESTAMP DEFAULT NOW()
);
```

`db.init_db()` runs `CREATE TABLE IF NOT EXISTS` on every app startup — no manual migration needed.

---

## User Flows

### Registration
1. User visits any route → if not logged in → redirect to `/login`
2. User clicks "Request access" → `/register` form (username, email, password, confirm password)
3. On submit: validate, hash password with bcrypt, insert `is_approved=false` row
4. Send email to `ADMIN_EMAIL`: "New registration from {username} — approve at {APP_URL}/admin/users"
5. Show `/pending` page: "Your account is awaiting admin approval."

### Login
1. POST `/login` with username + password
2. Validate credentials, check `is_approved`:
   - Approved (or admin) → create session via Flask-Login, redirect to `/`
   - Pending → flash "Your account is awaiting admin approval."
   - Wrong credentials → flash "Invalid username or password."

### Admin approval
1. Admin navigates to `/admin/users` (requires `is_admin=True`)
2. Sees table of pending users: username, email, registered date
3. Click "Approve" → `POST /admin/approve/<id>` → set `is_approved=true`, send approval email to user
4. Click "Reject" → `POST /admin/reject/<id>` → delete user row

### First admin setup
After DB is initialized, run via Railway's psql console:
```sql
UPDATE users SET is_admin=true WHERE username='your_username';
```

---

## Environment Variables (set on Railway)

| Variable       | Purpose                                                    |
|----------------|------------------------------------------------------------|
| `DATABASE_URL` | Auto-set by Railway PostgreSQL plugin                      |
| `SECRET_KEY`   | Flask session secret (generate with `python3 -c "import secrets; print(secrets.token_hex(32))"`) |
| `SMTP_HOST`    | SMTP server hostname (e.g. smtp.mailgun.org)               |
| `SMTP_PORT`    | SMTP port (587 for TLS)                                    |
| `SMTP_USER`    | SMTP username                                              |
| `SMTP_PASS`    | SMTP password                                              |
| `SMTP_FROM`    | From address for emails                                    |
| `ADMIN_EMAIL`  | Where to send new registration notifications               |
| `APP_URL`      | Public Railway URL (for links in emails)                   |
| `FRED_API_KEY` | Already exists — no change                                 |
| `PORT`         | Already exists — Flask uses it                             |

---

## Verification Checklist

1. **Local test:** `pip install -r requirements.txt && DATABASE_URL=<local-pg> SECRET_KEY=dev python3 app.py`
2. **Visit `http://localhost:8080`** → should redirect to `/login`
3. **Register a test user** → check admin email notification arrives
4. **Login as unapproved user** → should see "awaiting approval" flash message
5. **Set first user as admin** via psql: `UPDATE users SET is_admin=true WHERE id=1;`
6. **Login as admin** → visit `/admin/users` → approve the pending user
7. **Check approval email** arrives at the registered email
8. **Login as approved user** → should see the dashboard (`index.html`)
9. **Test `/fred` proxy** with a logged-in session → FRED data loads correctly
10. **Railway deploy:** Push to GitHub, verify Railway builds and runs, test the live URL
