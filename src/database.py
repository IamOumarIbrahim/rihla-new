import os
import sqlite3
from contextlib import contextmanager

from config import ROLES, DEMO_ACCOUNTS

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")


@contextmanager
def _connect():
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

        conn.execute('''
            CREATE TABLE IF NOT EXISTS venues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT,
                vendor_email TEXT
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT,
                price TEXT,
                description TEXT,
                vendor_email TEXT,
                venue_id INTEGER,
                event_datetime TEXT,
                is_recurring TEXT,
                recur_day TEXT,
                recur_time TEXT,
                FOREIGN KEY(venue_id) REFERENCES venues(id)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS vendor_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_email TEXT NOT NULL,
                name TEXT NOT NULL
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_code TEXT UNIQUE,
                event_title TEXT,
                customer_email TEXT,
                status TEXT DEFAULT 'Valid'
            )
        ''')

        user_columns = [row[1] for row in conn.execute("PRAGMA table_info(users)")]
        if "role" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'Customer'")
        if "phone" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN phone TEXT")

        event_columns = [row[1] for row in conn.execute("PRAGMA table_info(events)")]
        if "venue_id" not in event_columns:
            conn.execute("ALTER TABLE events ADD COLUMN venue_id INTEGER")
        if "event_datetime" not in event_columns:
            conn.execute("ALTER TABLE events ADD COLUMN event_datetime TEXT")
        if "is_recurring" not in event_columns:
            conn.execute("ALTER TABLE events ADD COLUMN is_recurring TEXT")
        if "recur_day" not in event_columns:
            conn.execute("ALTER TABLE events ADD COLUMN recur_day TEXT")
        if "recur_time" not in event_columns:
            conn.execute("ALTER TABLE events ADD COLUMN recur_time TEXT")

        for role, (email, password) in DEMO_ACCOUNTS.items():
            try:
                conn.execute(
                    "INSERT INTO users (email, password, role, phone) VALUES (?, ?, ?, ?)",
                    (email, password, role, "+971 50 1234567"),
                )
            except sqlite3.IntegrityError:
                conn.execute("UPDATE users SET role = ?, phone = ? WHERE email = ?", (role, "+971 50 1234567", email))

        cursor = conn.cursor()
        
        # Clear old seed data or update existing demo entries if needed
        cursor.execute("SELECT COUNT(*) FROM venues")
        if cursor.fetchone()[0] == 0:
            conn.execute("INSERT INTO venues (name, address, vendor_email) VALUES (?, ?, ?)", 
                         ("Burj Khalifa", "Dubai Downtown, Dubai, Sharjah", "vendor@email.com"))
            conn.execute("INSERT INTO venues (name, address, vendor_email) VALUES (?, ?, ?)", 
                         ("Dubai Desert Conservation Reserve", "Al Ain Road, Dubai", "vendor@email.com"))

        cursor.execute("SELECT COUNT(*) FROM vendor_categories")
        if cursor.fetchone()[0] == 0:
            default_cats = [
                ("vendor@email.com", "Evening Safari"),
                ("vendor@email.com", "New Year Dinner"),
                ("vendor@email.com", "Overnight Camp")
            ]
            conn.executemany("INSERT INTO vendor_categories (vendor_email, name) VALUES (?, ?)", default_cats)

        cursor.execute("SELECT COUNT(*) FROM events")
        if cursor.fetchone()[0] == 0:
            demo_events = [
                ("New year dinner", "New Year Dinner", "500 AED", "Exclusive dining experience at the top with fireworks view.", "vendor@email.com", 1, "31st dec 2026 11:00pm", "One-Time", "N/A", "23:00"),
                ("Red Dune Sunset Safari and Royal BBQ Dinner", "Evening Safari", "240 AED", "Experience dune bashing, camel rides, and traditional buffet dinners under the desert stars.", "vendor@email.com", 2, "2026-11-05 15:30", "Recurring", "Tuesday, Thursday", "15:30")
            ]
            conn.executemany("INSERT INTO events (title, category, price, description, vendor_email, venue_id, event_datetime, is_recurring, recur_day, recur_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", demo_events)

        cursor.execute("SELECT COUNT(*) FROM tickets")
        if cursor.fetchone()[0] == 0:
            conn.execute(
                "INSERT INTO tickets (ticket_code, event_title, customer_email, status) VALUES (?, ?, ?, ?)",
                ("1234567890123456", "New year dinner", "customer@email.com", "Valid")
            )

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

def get_all_venues():
    with _connect() as conn:
        rows = conn.execute("SELECT id, name, address FROM venues").fetchall()
    return [{"id": r[0], "name": r[1], "address": r[2]} for r in rows]

def get_venues_by_vendor(vendor_email):
    with _connect() as conn:
        rows = conn.execute("SELECT id, name, address FROM venues WHERE vendor_email = ?", (vendor_email,)).fetchall()
    return [{"id": r[0], "name": r[1], "address": r[2]} for r in rows]

def create_venue(name, address, vendor_email):
    with _connect() as conn:
        conn.execute("INSERT INTO venues (name, address, vendor_email) VALUES (?, ?, ?)", (name, address, vendor_email))

def create_event(title, category, price, description, vendor_email, venue_id, event_datetime, is_recurring, recur_day, recur_time):
    with _connect() as conn:
        conn.execute(
            "INSERT INTO events (title, category, price, description, vendor_email, venue_id, event_datetime, is_recurring, recur_day, recur_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (title, category, price, description, vendor_email, venue_id, event_datetime, is_recurring, recur_day, recur_time)
        )

def get_all_events():
    with _connect() as conn:
        rows = conn.execute('''
            SELECT e.id, e.title, e.category, e.price, e.description, e.vendor_email, v.name, e.event_datetime, e.is_recurring, e.recur_day, e.recur_time, e.venue_id
            FROM events e LEFT JOIN venues v ON e.venue_id = v.id
        ''').fetchall()
    return [{"id": r[0], "title": r[1], "category": r[2], "price": r[3], "desc": r[4], "vendor_email": r[5], "venue_name": r[6], "event_datetime": r[7], "is_recurring": r[8], "recur_day": r[9], "recur_time": r[10], "venue_id": r[11]} for r in rows]

def get_events_by_vendor(vendor_email):
    with _connect() as conn:
        rows = conn.execute('''
            SELECT e.id, e.title, e.category, e.price, e.description, e.vendor_email, v.name, e.event_datetime, e.is_recurring, e.recur_day, e.recur_time, e.venue_id
            FROM events e LEFT JOIN venues v ON e.venue_id = v.id WHERE e.vendor_email = ?
        ''', (vendor_email,)).fetchall()
    return [{"id": r[0], "title": r[1], "category": r[2], "price": r[3], "desc": r[4], "vendor_email": r[5], "venue_name": r[6], "event_datetime": r[7], "is_recurring": r[8], "recur_day": r[9], "recur_time": r[10], "venue_id": r[11]} for r in rows]

def get_events_by_venue(venue_id):
    with _connect() as conn:
        rows = conn.execute('''
            SELECT id, title, category, price, description, vendor_email, venue_id, event_datetime, is_recurring, recur_day, recur_time
            FROM events WHERE venue_id = ?
        ''', (venue_id,)).fetchall()
    return [{"id": r[0], "title": r[1], "category": r[2], "price": r[3], "desc": r[4], "vendor_email": r[5], "venue_id": r[6], "event_datetime": r[7], "is_recurring": r[8], "recur_day": r[9], "recur_time": r[10]} for r in rows]

def update_event(event_id, title, category, price, description, venue_id, event_datetime, is_recurring, recur_day, recur_time):
    with _connect() as conn:
        conn.execute(
            "UPDATE events SET title = ?, category = ?, price = ?, description = ?, venue_id = ?, event_datetime = ?, is_recurring = ?, recur_day = ?, recur_time = ? WHERE id = ?",
            (title, category, price, description, venue_id, event_datetime, is_recurring, recur_day, recur_time, event_id)
        )

def delete_event(event_id):
    with _connect() as conn:
        conn.execute("DELETE FROM events WHERE id = ?", (event_id,))

def get_vendor_categories(vendor_email):
    with _connect() as conn:
        rows = conn.execute("SELECT id, name FROM vendor_categories WHERE vendor_email = ?", (vendor_email,)).fetchall()
    return [{"id": r[0], "name": r[1]} for r in rows]

def add_vendor_category(vendor_email, name):
    try:
        with _connect() as conn:
            conn.execute("INSERT INTO vendor_categories (vendor_email, name) VALUES (?, ?)", (vendor_email, name))
    except Exception:
        pass

def delete_vendor_category(category_id):
    with _connect() as conn:
        conn.execute("DELETE FROM vendor_categories WHERE id = ?", (category_id,))

def verify_ticket_code(ticket_code):
    with _connect() as conn:
        row = conn.execute(
            "SELECT event_title, customer_email, status FROM tickets WHERE ticket_code = ?", (ticket_code,)
        ).fetchone()
    if not row:
        return {"success": False, "message": "Invalid ticket code. Not found in system."}
    
    event_title, customer_email, status = row
    if status == "Used":
        return {"success": False, "message": "Ticket already used! Checked in previously."}
    
    with _connect() as conn:
        conn.execute("UPDATE tickets SET status = 'Used' WHERE ticket_code = ?", (ticket_code,))
    
    return {"success": True, "message": f"Access granted! Ticket valid for {event_title} ({customer_email})."}

def delete_venue(venue_id):
    with _connect() as conn:
        conn.execute("DELETE FROM venues WHERE id = ?", (venue_id,))