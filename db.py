"""
PostgreSQL connection and user query helpers.
Uses psycopg2 with DATABASE_URL from environment.
"""
import os
import psycopg2
import psycopg2.extras


def get_db_connection():
    """Return a new psycopg2 connection using DATABASE_URL."""
    return psycopg2.connect(os.environ["DATABASE_URL"])


def init_db():
    """Create the users table if it doesn't already exist."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id            SERIAL PRIMARY KEY,
                    username      VARCHAR(64) UNIQUE NOT NULL,
                    email         VARCHAR(120) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_approved   BOOLEAN DEFAULT FALSE,
                    is_admin      BOOLEAN DEFAULT FALSE,
                    created_at    TIMESTAMP DEFAULT NOW()
                );
            """)
        conn.commit()
    finally:
        conn.close()


def get_user_by_username(username):
    """Return a user row dict for the given username, or None."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            return cur.fetchone()
    finally:
        conn.close()


def get_user_by_id(user_id):
    """Return a user row dict for the given id, or None."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            return cur.fetchone()
    finally:
        conn.close()


def create_user(username, email, password_hash):
    """Insert a new unapproved user. Returns the new user's id."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                (username, email, password_hash),
            )
            user_id = cur.fetchone()[0]
        conn.commit()
        return user_id
    finally:
        conn.close()


def approve_user(user_id):
    """Set is_approved=true for the given user id."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET is_approved = TRUE WHERE id = %s", (user_id,))
        conn.commit()
    finally:
        conn.close()


def reject_user(user_id):
    """Delete the user with the given id (rejection = removal)."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
    finally:
        conn.close()


def get_pending_users():
    """Return all unapproved, non-admin users ordered by registration date."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, username, email, created_at FROM users WHERE is_approved = FALSE AND is_admin = FALSE ORDER BY created_at"
            )
            return cur.fetchall()
    finally:
        conn.close()
