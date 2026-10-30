import hashlib
import hmac
from datetime import date
import os
import secrets
import sqlite3
from contextlib import contextmanager

from config import ROLES, DEMO_ACCOUNTS

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")
# Server-side: DB always lives next to this file (server/users.db)

# Guests an event can take on one date when no vehicles are assigned to it.
DEFAULT_EVENT_CAPACITY = 20
MAX_EVENT_CAPACITY = 5000
MAX_GUESTS_PER_BOOKING = 10
MAX_OPEN_SUPPORT_TICKETS = 3


@contextmanager
def _connect():
    """Server-side: always connects to the server's own DB_PATH."""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


_HASH_PREFIX = "pbkdf2$"
_HASH_ROUNDS = 200_000


def hash_password(password):
    """Salted PBKDF2 hash, so passwords are never stored as plain text."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), _HASH_ROUNDS)
    return f"{_HASH_PREFIX}{_HASH_ROUNDS}${salt}${digest.hex()}"


def verify_password(password, stored):
    if not stored:
        return False
    if not stored.startswith(_HASH_PREFIX):
        # Old row created before hashing was added (plain text).
        return hmac.compare_digest(password.encode("utf-8"), stored.encode("utf-8"))
    try:
        _, rounds, salt, digest = stored.split("$")
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), int(rounds))
    except ValueError:
        return False
    return hmac.compare_digest(candidate.hex(), digest)


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
                capacity INTEGER NOT NULL DEFAULT 20,
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

        conn.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_email TEXT NOT NULL,
                event_id INTEGER,
                event_title TEXT NOT NULL,
                venue_name TEXT,
                booking_date TEXT NOT NULL,
                event_time TEXT,
                guests INTEGER NOT NULL DEFAULT 1,
                total_price INTEGER NOT NULL DEFAULT 0,
                ticket_code TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL DEFAULT 'Confirmed',
                client_name TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(event_id) REFERENCES events(id)
            )
        ''')
        conn.execute("CREATE INDEX IF NOT EXISTS idx_bookings_customer ON bookings(customer_email)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_bookings_event ON bookings(event_id, booking_date)")

        conn.execute('''
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_email TEXT NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Open',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                resolved_by TEXT,
                resolved_at TEXT
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS vehicle_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                capacity INTEGER NOT NULL
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_number TEXT UNIQUE NOT NULL,
                vehicle_type TEXT NOT NULL,
                location TEXT NOT NULL,
                status TEXT DEFAULT 'Available',
                dispatcher_email TEXT,
                auto_reassign_recurring INTEGER DEFAULT 0
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS event_vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                vehicle_id INTEGER,
                status TEXT DEFAULT 'Assigned',
                FOREIGN KEY(event_id) REFERENCES events(id),
                FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
            )
        ''')

        # Databases made before event capacity existed get the new column (old events start at 20).
        event_columns = [row[1] for row in conn.execute("PRAGMA table_info(events)")]
        if "capacity" not in event_columns:
            conn.execute(f"ALTER TABLE events ADD COLUMN capacity INTEGER NOT NULL DEFAULT {DEFAULT_EVENT_CAPACITY}")

        # Check bookings table for client_name column
        booking_columns = [row[1] for row in conn.execute("PRAGMA table_info(bookings)")]
        if "client_name" not in booking_columns:
            conn.execute("ALTER TABLE bookings ADD COLUMN client_name TEXT DEFAULT ''")

        conn.execute('''
            CREATE TABLE IF NOT EXISTS partner_cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_email TEXT NOT NULL,
                event_id INTEGER NOT NULL,
                booking_date TEXT NOT NULL,
                guests INTEGER NOT NULL DEFAULT 1,
                client_name TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(event_id) REFERENCES events(id)
            )
        ''')
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cart_partner ON partner_cart(partner_email)")

        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM vehicle_types")
        if cursor.fetchone()[0] == 0:
            default_vehicle_types = [
                ("desert buggy", 2),
                ("4x4 toyota landcrusier", 6),
                ("mini-yacht", 20),
                ("tesla sedan", 4),
                ("RTA bus", 50)
            ]
            conn.executemany("INSERT OR IGNORE INTO vehicle_types (name, capacity) VALUES (?, ?)", default_vehicle_types)

        cursor.execute("SELECT COUNT(*) FROM venues")
        if cursor.fetchone()[0] == 0:
            conn.execute("INSERT INTO venues (name, address, vendor_email) VALUES (?, ?, ?)", 
                         ("Burj Khalifa", "Dubai Downtown, Dubai", "vendor@email.com"))
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
                ("New year dinner", "New Year Dinner", "500 AED", "Exclusive dining experience at the top with fireworks view.", "vendor@email.com", 1, "2026-12-31 23:00", "One-Time", "N/A", "23:00", 40),
                ("Red Dune Sunset Safari and Royal BBQ Dinner", "Evening Safari", "240 AED", "Experience dune bashing, camel rides, and traditional buffet dinners under the desert stars.", "vendor@email.com", 2, "2026-11-05 15:30", "Recurring", "Tuesday, Thursday", "15:30", 30)
            ]
            conn.executemany("INSERT INTO events (title, category, price, description, vendor_email, venue_id, event_datetime, is_recurring, recur_day, recur_time, capacity) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", demo_events)

        cursor.execute("SELECT COUNT(*) FROM vehicles")
        if cursor.fetchone()[0] == 0:
            demo_vehicles = [
                ("10045", "desert buggy", "Dubai Desert Conservation Reserve", "Available", "dispatcher@email.com", 0),
                ("20391", "4x4 toyota landcrusier", "Dubai Desert Conservation Reserve", "Available", "dispatcher@email.com", 1),
                ("30482", "mini-yacht", "Dubai Marina Pier 7", "Available", "dispatcher@email.com", 0),
                ("40593", "tesla sedan", "Dubai Downtown", "Available", "dispatcher@email.com", 0),
                ("50604", "RTA bus", "Sharjah Station", "Available", "dispatcher@email.com", 1),
                ("60715", "desert buggy", "Al Badayer Oasis", "Available", "dispatcher@email.com", 0),
                ("70826", "4x4 toyota landcrusier", "Liwa Desert", "Available", "dispatcher@email.com", 1)
            ]
            conn.executemany("INSERT INTO vehicles (license_number, vehicle_type, location, status, dispatcher_email, auto_reassign_recurring) VALUES (?, ?, ?, ?, ?, ?)", demo_vehicles)

        cursor.execute("SELECT COUNT(*) FROM tickets")
        if cursor.fetchone()[0] == 0:
            conn.execute(
                "INSERT INTO tickets (ticket_code, event_title, customer_email, status) VALUES (?, ?, ?, ?)",
                ("1234567890123456", "New year dinner", "customer@email.com", "Valid")
            )

        # Link the demo ticket to a real booking, so "My Bookings" has something to show.
        demo_code = "1234567890123456"
        demo_ticket = conn.execute("SELECT 1 FROM tickets WHERE ticket_code = ?", (demo_code,)).fetchone()
        demo_booked = conn.execute("SELECT 1 FROM bookings WHERE ticket_code = ?", (demo_code,)).fetchone()
        demo_event = conn.execute(
            "SELECT e.id, e.title, e.recur_time, v.name FROM events e LEFT JOIN venues v ON v.id = e.venue_id "
            "WHERE e.title = 'New year dinner'"
        ).fetchone()
        if demo_ticket and not demo_booked and demo_event:
            conn.execute(
                "INSERT INTO bookings (customer_email, event_id, event_title, venue_name, booking_date, event_time, "
                "guests, total_price, ticket_code, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Confirmed')",
                ("customer@email.com", demo_event[0], demo_event[1], demo_event[3], "2026-12-31", demo_event[2] or "23:00", 2, 1000, demo_code),
            )

        # Fix the wrong address that older versions saved for the first venue.
        conn.execute("UPDATE venues SET address = 'Dubai Downtown, Dubai' WHERE address = 'Dubai Downtown, Dubai, Sharjah'")

        # The demo accounts on the login screen must really exist in the database.
        for demo_role, (demo_email, demo_password) in DEMO_ACCOUNTS.items():
            exists = conn.execute("SELECT 1 FROM users WHERE lower(email) = ?", (demo_email.lower(),)).fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO users (email, password, role, phone) VALUES (?, ?, ?, ?)",
                    (demo_email, hash_password(demo_password), demo_role, None),
                )


def register_user(email, password, role="Customer", phone=None):
    if role not in ROLES:
        role = "Customer"
    email = (email or "").strip().lower()
    if not email or not password or email_exists(email):
        return False
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO users (email, password, role, phone) VALUES (?, ?, ?, ?)",
                (email, hash_password(password), role, phone),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def check_login(email, password):
    email = (email or "").strip()
    with _connect() as conn:
        row = conn.execute(
            "SELECT email, password FROM users WHERE lower(email) = lower(?)", (email,)
        ).fetchone()
        if row is None or not verify_password(password, row[1]):
            return False
        if not row[1].startswith(_HASH_PREFIX):
            # Upgrade an old plain-text password to a salted hash after a successful login.
            conn.execute("UPDATE users SET password = ? WHERE email = ?", (hash_password(password), row[0]))
    return True


def get_user_email(email):
    """Returns the email exactly as stored (the typed letter case does not matter), or None."""
    with _connect() as conn:
        row = conn.execute("SELECT email FROM users WHERE lower(email) = lower(?)", ((email or "").strip(),)).fetchone()
    return row[0] if row else None


def get_role(email):
    with _connect() as conn:
        row = conn.execute("SELECT role FROM users WHERE lower(email) = lower(?)", ((email or "").strip(),)).fetchone()
    return row[0] if row and row[0] else "Customer"


def get_password_by_email(email):
    with _connect() as conn:
        row = conn.execute("SELECT password FROM users WHERE email = ?", (email,)).fetchone()
    return row[0] if row else None


def update_password(email, new_password):
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET password = ? WHERE lower(email) = lower(?)",
            (hash_password(new_password), (email or "").strip()),
        )


def email_exists(email):
    with _connect() as conn:
        row = conn.execute("SELECT 1 FROM users WHERE lower(email) = lower(?)", ((email or "").strip(),)).fetchone()
    return row is not None


def phone_exists(phone):
    with _connect() as conn:
        row = conn.execute("SELECT 1 FROM users WHERE phone = ?", (phone,)).fetchone()
    return row is not None


# --- Support Tickets ---
def create_support_ticket(customer_email, subject, message):
    customer_email = (customer_email or "").strip()
    subject = (subject or "").strip()
    message = (message or "").strip()

    if not subject or not message:
        return {"success": False, "message": "Subject and message are required."}
    if len(subject) < 3:
        return {"success": False, "message": "Subject must be at least 3 characters."}
    if len(message) < 10:
        return {"success": False, "message": "Message must be at least 10 characters."}

    with _connect() as conn:
        open_count = conn.execute(
            "SELECT COUNT(*) FROM support_tickets WHERE lower(customer_email) = lower(?) AND status = 'Open'",
            (customer_email,),
        ).fetchone()[0]
        if open_count >= MAX_OPEN_SUPPORT_TICKETS:
            return {
                "success": False,
                "message": f"You already have {MAX_OPEN_SUPPORT_TICKETS} open tickets. Please wait for staff to reply.",
            }

        cursor = conn.execute(
            "INSERT INTO support_tickets (customer_email, subject, message, status) VALUES (?, ?, ?, 'Open')",
            (customer_email, subject, message),
        )
        ticket_id = cursor.lastrowid
    return {"success": True, "message": "Support ticket created.", "ticket_id": ticket_id}


def get_support_tickets_by_customer(customer_email):
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, subject, message, status, created_at FROM support_tickets "
            "WHERE lower(customer_email) = lower(?) ORDER BY id DESC",
            ((customer_email or "").strip(),),
        ).fetchall()
    return [{"id": r[0], "subject": r[1], "message": r[2], "status": r[3], "created_at": r[4]} for r in rows]


def get_open_support_tickets():
    """Oldest first, so the longest waiting customer is answered first."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, customer_email, subject, message, created_at FROM support_tickets "
            "WHERE status = 'Open' ORDER BY id"
        ).fetchall()
    return [{"id": r[0], "customer_email": r[1], "subject": r[2], "message": r[3], "created_at": r[4]} for r in rows]


def resolve_support_ticket(ticket_id, staff_email):
    with _connect() as conn:
        updated = conn.execute(
            "UPDATE support_tickets SET status = 'Resolved', resolved_by = ?, resolved_at = CURRENT_TIMESTAMP "
            "WHERE id = ? AND status = 'Open'",
            ((staff_email or "").strip(), ticket_id),
        ).rowcount
    return bool(updated)
