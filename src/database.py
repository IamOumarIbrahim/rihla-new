import hashlib
import hmac
import os
import secrets
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
                ("New year dinner", "New Year Dinner", "500 AED", "Exclusive dining experience at the top with fireworks view.", "vendor@email.com", 1, "2026-12-31 23:00", "One-Time", "N/A", "23:00"),
                ("Red Dune Sunset Safari and Royal BBQ Dinner", "Evening Safari", "240 AED", "Experience dune bashing, camel rides, and traditional buffet dinners under the desert stars.", "vendor@email.com", 2, "2026-11-05 15:30", "Recurring", "Tuesday, Thursday", "15:30")
            ]
            conn.executemany("INSERT INTO events (title, category, price, description, vendor_email, venue_id, event_datetime, is_recurring, recur_day, recur_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", demo_events)

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

def delete_venue(venue_id):
    """Returns False (and deletes nothing) while events still use this venue."""
    with _connect() as conn:
        in_use = conn.execute("SELECT 1 FROM events WHERE venue_id = ? LIMIT 1", (venue_id,)).fetchone()
        if in_use:
            return False
        conn.execute("DELETE FROM venues WHERE id = ?", (venue_id,))
    return True

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
        # Release vehicles dispatched to this event so they do not stay "Assigned" forever.
        conn.execute(
            "UPDATE vehicles SET status = 'Available' WHERE status = 'Assigned' AND id IN "
            "(SELECT vehicle_id FROM event_vehicles WHERE event_id = ? AND status = 'Assigned')",
            (event_id,),
        )
        conn.execute("DELETE FROM event_vehicles WHERE event_id = ?", (event_id,))
        conn.execute("DELETE FROM events WHERE id = ?", (event_id,))

def get_vendor_categories(vendor_email):
    with _connect() as conn:
        rows = conn.execute("SELECT id, name FROM vendor_categories WHERE vendor_email = ?", (vendor_email,)).fetchall()
    return [{"id": r[0], "name": r[1]} for r in rows]

def add_vendor_category(vendor_email, name):
    """Returns False when this vendor already has a category with the same name."""
    name = name.strip()
    with _connect() as conn:
        duplicate = conn.execute(
            "SELECT 1 FROM vendor_categories WHERE vendor_email = ? AND lower(name) = lower(?)",
            (vendor_email, name),
        ).fetchone()
        if duplicate:
            return False
        conn.execute("INSERT INTO vendor_categories (vendor_email, name) VALUES (?, ?)", (vendor_email, name))
    return True

def delete_vendor_category(category_id):
    with _connect() as conn:
        conn.execute("DELETE FROM vendor_categories WHERE id = ?", (category_id,))

def verify_ticket_code(ticket_code, expected_event_title=None):
    with _connect() as conn:
        row = conn.execute(
            "SELECT event_title, customer_email, status FROM tickets WHERE ticket_code = ?", (ticket_code,)
        ).fetchone()
    if not row:
        return {"success": False, "message": "Invalid ticket code. Not found in system."}
    
    event_title, customer_email, status = row
    if expected_event_title and event_title != expected_event_title:
        return {"success": False, "message": f"Wrong event. This ticket is for {event_title}."}
    if status == "Used":
        return {"success": False, "message": "Ticket already used! Checked in previously."}
    
    with _connect() as conn:
        # One atomic update, so two scanners cannot both accept the same ticket.
        cursor = conn.execute(
            "UPDATE tickets SET status = 'Used' WHERE ticket_code = ? AND COALESCE(status, '') != 'Used'",
            (ticket_code,),
        )
        updated = cursor.rowcount
    if not updated:
        return {"success": False, "message": "Ticket already used! Checked in previously."}
    
    return {"success": True, "message": f"Access granted! Ticket valid for {event_title} ({customer_email})."}

def get_vehicle_types():
    with _connect() as conn:
        rows = conn.execute("SELECT id, name, capacity FROM vehicle_types").fetchall()
    return [{"id": r[0], "name": r[1], "capacity": r[2]} for r in rows]

def get_vehicle_capacity(vehicle_type):
    with _connect() as conn:
        row = conn.execute("SELECT capacity FROM vehicle_types WHERE name = ?", (vehicle_type,)).fetchone()
    return row[0] if row else 4

def get_all_vehicles(dispatcher_email):
    with _connect() as conn:
        rows = conn.execute('''
            SELECT v.id, v.license_number, v.vehicle_type, v.location, v.status, v.auto_reassign_recurring, vt.capacity
            FROM vehicles v LEFT JOIN vehicle_types vt ON v.vehicle_type = vt.name
            WHERE v.dispatcher_email = ?
        ''', (dispatcher_email,)).fetchall()
    return [{"id": r[0], "license_number": r[1], "vehicle_type": r[2], "location": r[3], "status": r[4], "auto_reassign_recurring": r[5], "capacity": r[6] if r[6] is not None else 4} for r in rows]

def create_vehicle(license_number, vehicle_type, location, dispatcher_email, auto_reassign_recurring):
    with _connect() as conn:
        conn.execute("INSERT INTO vehicles (license_number, vehicle_type, location, status, dispatcher_email, auto_reassign_recurring) VALUES (?, ?, ?, 'Available', ?, ?)",
                     (license_number, vehicle_type, location, dispatcher_email, auto_reassign_recurring))

def delete_vehicle(vehicle_id):
    with _connect() as conn:
        conn.execute("DELETE FROM event_vehicles WHERE vehicle_id = ?", (vehicle_id,))
        conn.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))

def update_vehicle_status(vehicle_id, status):
    with _connect() as conn:
        if status != "Assigned":
            # A vehicle that is no longer assigned must not stay linked to an event.
            conn.execute(
                "UPDATE event_vehicles SET status = 'Concluded' WHERE vehicle_id = ? AND status = 'Assigned'",
                (vehicle_id,),
            )
        conn.execute("UPDATE vehicles SET status = ? WHERE id = ?", (status, vehicle_id))

def dispatch_vehicle_combination(event_id, vehicle_assignments):
    """Assigns only vehicles that are still Available. Returns how many were assigned."""
    assigned = 0
    with _connect() as conn:
        for item in vehicle_assignments:
            vid = item["vehicle_id"]
            reassign = item["auto_reassign_recurring"]
            updated = conn.execute(
                "UPDATE vehicles SET status = 'Assigned', auto_reassign_recurring = ? WHERE id = ? AND status = 'Available'",
                (reassign, vid),
            ).rowcount
            if updated:
                conn.execute("INSERT INTO event_vehicles (event_id, vehicle_id, status) VALUES (?, ?, 'Assigned')", (event_id, vid))
                assigned += 1
    return assigned

def free_vehicle(vehicle_id):
    with _connect() as conn:
        conn.execute("UPDATE event_vehicles SET status = 'Concluded' WHERE vehicle_id = ? AND status = 'Assigned'", (vehicle_id,))
        conn.execute("UPDATE vehicles SET status = 'Available' WHERE id = ?", (vehicle_id,))