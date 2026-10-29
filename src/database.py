import os
import sqlite3
from contextlib import contextmanager

from config import ROLES, DEMO_ACCOUNTS

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")


@contextmanager
def _connect():
    """Open the database, commit on success, always close."""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with _connect() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                email TEXT UNIQUE,
                password TEXT,
                role TEXT NOT NULL DEFAULT 'Customer',
                phone TEXT
            )
        ''')

        columns = [row[1] for row in conn.execute("PRAGMA table_info(users)")]
        if "role" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'Customer'")
        if "phone" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN phone TEXT")

        for role, (email, password) in DEMO_ACCOUNTS.items():
            try:
                conn.execute(
                    "INSERT INTO users (email, password, role, phone) VALUES (?, ?, ?, ?)",
                    (email, password, role, "+971 50 1234567"),
                )
            except sqlite3.IntegrityError:
                conn.execute("UPDATE users SET role = ?, phone = ? WHERE email = ?", (role, "+971 50 1234567", email))

def register_user(email, password, role="Customer", phone=None):
    if role not in ROLES:
        role = "Customer"
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO users (email, password, role, phone) VALUES (?, ?, ?, ?)",
                (email, password, role, phone),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def check_login(email, password):
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE email = ? AND password = ?", (email, password)
        ).fetchone()
    return row is not None


def get_role(email):
    with _connect() as conn:
        row = conn.execute("SELECT role FROM users WHERE email = ?", (email,)).fetchone()
    return row[0] if row and row[0] else "Customer"


def get_password_by_email(email):
    with _connect() as conn:
        row = conn.execute("SELECT password FROM users WHERE email = ?", (email,)).fetchone()
    return row[0] if row else None


def update_password(email, new_password):
    with _connect() as conn:
        conn.execute("UPDATE users SET password = ? WHERE email = ?", (new_password, email))

def email_exists(email):
    with _connect() as conn:
        row = conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone()
    return row is not None

def phone_exists(phone):
    with _connect() as conn:
        row = conn.execute("SELECT 1 FROM users WHERE phone = ?", (phone,)).fetchone()
    return row is not None