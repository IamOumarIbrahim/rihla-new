import hashlib
import hmac
from datetime import date
import os
import secrets
import sqlite3
from contextlib import contextmanager

from config import ROLES, DEMO_ACCOUNTS

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")

# Guests an event can take on one date when no vehicles are assigned to it.
DEFAULT_EVENT_CAPACITY = 20
MAX_EVENT_CAPACITY = 5000


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

def _capacity_or_default(value):
    """None -> the default capacity. Anything else must be a whole number from 1 to MAX_EVENT_CAPACITY."""
    if value is None:
        return DEFAULT_EVENT_CAPACITY
    value = int(value)
    if not 1 <= value <= MAX_EVENT_CAPACITY:
        raise ValueError(f"Capacity must be between 1 and {MAX_EVENT_CAPACITY}.")
    return value

def create_event(title, category, price, description, vendor_email, venue_id, event_datetime, is_recurring, recur_day, recur_time, capacity=None):
    capacity = _capacity_or_default(capacity)
    with _connect() as conn:
        conn.execute(
            "INSERT INTO events (title, category, price, description, vendor_email, venue_id, event_datetime, is_recurring, recur_day, recur_time, capacity) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (title, category, price, description, vendor_email, venue_id, event_datetime, is_recurring, recur_day, recur_time, capacity)
        )

def get_all_events():
    with _connect() as conn:
        rows = conn.execute('''
            SELECT e.id, e.title, e.category, e.price, e.description, e.vendor_email, v.name, e.event_datetime, e.is_recurring, e.recur_day, e.recur_time, e.venue_id, e.capacity
            FROM events e LEFT JOIN venues v ON e.venue_id = v.id
        ''').fetchall()
    return [{"id": r[0], "title": r[1], "category": r[2], "price": r[3], "desc": r[4], "vendor_email": r[5], "venue_name": r[6], "event_datetime": r[7], "is_recurring": r[8], "recur_day": r[9], "recur_time": r[10], "venue_id": r[11], "capacity": r[12]} for r in rows]

def get_events_by_vendor(vendor_email):
    with _connect() as conn:
        rows = conn.execute('''
            SELECT e.id, e.title, e.category, e.price, e.description, e.vendor_email, v.name, e.event_datetime, e.is_recurring, e.recur_day, e.recur_time, e.venue_id, e.capacity
            FROM events e LEFT JOIN venues v ON e.venue_id = v.id WHERE e.vendor_email = ?
        ''', (vendor_email,)).fetchall()
    return [{"id": r[0], "title": r[1], "category": r[2], "price": r[3], "desc": r[4], "vendor_email": r[5], "venue_name": r[6], "event_datetime": r[7], "is_recurring": r[8], "recur_day": r[9], "recur_time": r[10], "venue_id": r[11], "capacity": r[12]} for r in rows]

def get_events_by_venue(venue_id):
    with _connect() as conn:
        rows = conn.execute('''
            SELECT id, title, category, price, description, vendor_email, venue_id, event_datetime, is_recurring, recur_day, recur_time
            FROM events WHERE venue_id = ?
        ''', (venue_id,)).fetchall()
    return [{"id": r[0], "title": r[1], "category": r[2], "price": r[3], "desc": r[4], "vendor_email": r[5], "venue_id": r[6], "event_datetime": r[7], "is_recurring": r[8], "recur_day": r[9], "recur_time": r[10]} for r in rows]

def update_event(event_id, title, category, price, description, venue_id, event_datetime, is_recurring, recur_day, recur_time, capacity=None):
    """capacity=None keeps the capacity the event already has."""
    new_capacity = None if capacity is None else _capacity_or_default(capacity)
    with _connect() as conn:
        if new_capacity is not None:
            conn.execute("UPDATE events SET capacity = ? WHERE id = ?", (new_capacity, event_id))
        conn.execute(
            "UPDATE events SET title = ?, category = ?, price = ?, description = ?, venue_id = ?, event_datetime = ?, is_recurring = ?, recur_day = ?, recur_time = ? WHERE id = ?",
            (title, category, price, description, venue_id, event_datetime, is_recurring, recur_day, recur_time, event_id)
        )
        # The staff scanner compares event titles, so tickets and bookings must follow a new title.
        conn.execute("UPDATE bookings SET event_title = ? WHERE event_id = ?", (title, event_id))
        conn.execute(
            "UPDATE tickets SET event_title = ? WHERE ticket_code IN (SELECT ticket_code FROM bookings WHERE event_id = ?)",
            (title, event_id),
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
        # The organiser removed the event, so bookings with an unused ticket are cancelled.
        conn.execute(
            "UPDATE bookings SET status = 'Cancelled' WHERE event_id = ? AND status = 'Confirmed' "
            "AND ticket_code IN (SELECT ticket_code FROM tickets WHERE status = 'Valid')",
            (event_id,),
        )
        conn.execute(
            "UPDATE tickets SET status = 'Cancelled' WHERE status = 'Valid' "
            "AND ticket_code IN (SELECT ticket_code FROM bookings WHERE event_id = ? AND status = 'Cancelled')",
            (event_id,),
        )
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
    if status == "Cancelled":
        return {"success": False, "message": "This ticket was cancelled. Entry refused."}
    if status == "Used":
        return {"success": False, "message": "Ticket already used! Checked in previously."}
    
    with _connect() as conn:
        # One atomic update, so two scanners cannot both accept the same ticket.
        cursor = conn.execute(
            "UPDATE tickets SET status = 'Used' WHERE ticket_code = ? AND COALESCE(status, 'Valid') = 'Valid'",
            (ticket_code,),
        )
        updated = cursor.rowcount
    if not updated:
        return {"success": False, "message": "This ticket was just used or cancelled. Entry refused."}
    
    note = ""
    with _connect() as conn:
        booking = conn.execute("SELECT guests, booking_date FROM bookings WHERE ticket_code = ?", (ticket_code,)).fetchone()
    if booking:
        note = f" Admit {booking[0]} guest(s)."
        if booking[1] != date.today().isoformat():
            note += f" Note: this booking is for {booking[1]}, not today."
    return {"success": True, "message": f"Access granted! Ticket valid for {event_title} ({customer_email}).{note}"}

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


# ---------------------------------------------------------------- bookings
MAX_GUESTS_PER_BOOKING = 10
_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def price_to_int(value):
    """'240 AED' -> 240"""
    digits = "".join(c for c in str(value) if c in "0123456789")
    return int(digits) if digits else 0


def format_ticket_code(code):
    """'1234567890123456' -> '1234 5678 9012 3456'"""
    code = str(code)
    return " ".join(code[i:i + 4] for i in range(0, len(code), 4))


def _new_ticket_code(conn):
    while True:
        code = "".join(secrets.choice("0123456789") for _ in range(16))
        if not conn.execute("SELECT 1 FROM tickets WHERE ticket_code = ?", (code,)).fetchone():
            return code


def _event_allows_date(is_recurring, recur_day, event_datetime, day):
    if is_recurring == "Recurring":
        names = {d.strip() for d in (recur_day or "").split(",") if d.strip() in _WEEKDAYS}
        if names:
            return _WEEKDAYS[day.weekday()] in names
    return str(event_datetime or "")[:10] == day.isoformat()


def _capacity_info(conn, event_id, day=None):
    """How many guests an event can take on one date.

    With vehicles assigned, the seats of those vehicles are the limit (any mix of types).
    Without vehicles, the capacity the vendor typed in is the limit.
    With a day, 'booked' and 'remaining' count the confirmed guests of that date.
    """
    row = conn.execute("SELECT capacity FROM events WHERE id = ?", (event_id,)).fetchone()
    event_capacity = row[0] if row and row[0] is not None else DEFAULT_EVENT_CAPACITY
    rows = conn.execute(
        "SELECT v.vehicle_type, COUNT(*), COALESCE(vt.capacity, 4) FROM event_vehicles ev "
        "JOIN vehicles v ON v.id = ev.vehicle_id LEFT JOIN vehicle_types vt ON vt.name = v.vehicle_type "
        "WHERE ev.event_id = ? AND ev.status = 'Assigned' GROUP BY v.vehicle_type ORDER BY v.vehicle_type",
        (event_id,),
    ).fetchall()
    vehicles = [{"vehicle_type": r[0], "count": r[1], "seats_each": r[2]} for r in rows]
    if vehicles:
        total = sum(v["count"] * v["seats_each"] for v in vehicles)
        source = "vehicles"
    else:
        total = event_capacity
        source = "event"
    info = {"total": total, "source": source, "vehicles": vehicles, "booked": None, "remaining": None}
    if day is not None:
        booked = conn.execute(
            "SELECT COALESCE(SUM(guests), 0) FROM bookings WHERE event_id = ? AND booking_date = ? AND status = 'Confirmed'",
            (event_id, day.isoformat()),
        ).fetchone()[0]
        info["booked"] = booked
        info["remaining"] = max(0, total - booked)
    return info


def get_event_capacity(event_id, booking_date=None):
    """Capacity of one event: {"total", "source" ("vehicles" or "event"), "vehicles", "booked", "remaining"}.

    'booked' and 'remaining' are None unless a booking_date (date or 'YYYY-MM-DD') is given.
    """
    day = None
    if booking_date is not None:
        day = booking_date if isinstance(booking_date, date) else date.fromisoformat(str(booking_date))
    with _connect() as conn:
        return _capacity_info(conn, event_id, day)


def create_booking(customer_email, event_id, booking_date, guests):
    """Saves a booking and creates its 16-digit ticket code.

    Returns {"success": bool, "message": str, "booking": dict or None}.
    """
    def refuse(message):
        return {"success": False, "message": message, "booking": None}

    customer_email = (customer_email or "").strip()
    try:
        day = date.fromisoformat(str(booking_date))
        guests = int(guests)
    except (TypeError, ValueError):
        return refuse("Invalid date or number of guests.")
    if not customer_email:
        return refuse("You must be logged in to book.")
    if guests < 1 or guests > MAX_GUESTS_PER_BOOKING:
        return refuse(f"You can book 1 to {MAX_GUESTS_PER_BOOKING} guests at a time.")
    if day < date.today():
        return refuse("This date is in the past. Please choose another date.")

    with _connect() as conn:
        # Lock now, so two customers cannot both take the last seats.
        conn.execute("BEGIN IMMEDIATE")
        event = conn.execute(
            "SELECT e.title, e.price, e.is_recurring, e.recur_day, e.event_datetime, e.recur_time, v.name "
            "FROM events e LEFT JOIN venues v ON v.id = e.venue_id WHERE e.id = ?",
            (event_id,),
        ).fetchone()
        if not event:
            return refuse("This event no longer exists.")
        title, price, is_recurring, recur_day, event_datetime, recur_time, venue_name = event

        if not _event_allows_date(is_recurring, recur_day, event_datetime, day):
            return refuse("This event is not available on the date you chose.")

        already = conn.execute(
            "SELECT 1 FROM bookings WHERE lower(customer_email) = lower(?) AND event_id = ? "
            "AND booking_date = ? AND status = 'Confirmed'",
            (customer_email, event_id, day.isoformat()),
        ).fetchone()
        if already:
            return refuse("You already have a booking for this event on that date. See My Bookings.")

        capacity = _capacity_info(conn, event_id, day)
        if guests > capacity["remaining"]:
            if capacity["remaining"] == 0:
                return refuse(f"Sorry, this event is fully booked on that date (capacity {capacity['total']}).")
            return refuse(
                f"Not enough seats. Only {capacity['remaining']} of {capacity['total']} seats are left "
                f"on that date, and you asked for {guests}."
            )

        code = _new_ticket_code(conn)
        total = price_to_int(price) * guests
        event_time = recur_time or str(event_datetime or "")[11:16]

        conn.execute(
            "INSERT INTO tickets (ticket_code, event_title, customer_email, status) VALUES (?, ?, ?, 'Valid')",
            (code, title, customer_email),
        )
        cursor = conn.execute(
            "INSERT INTO bookings (customer_email, event_id, event_title, venue_name, booking_date, event_time, "
            "guests, total_price, ticket_code, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Confirmed')",
            (customer_email, event_id, title, venue_name, day.isoformat(), event_time, guests, total, code),
        )
        booking_id = cursor.lastrowid

    return {
        "success": True,
        "message": "Booking confirmed.",
        "booking": {
            "id": booking_id, "event_title": title, "venue_name": venue_name, "booking_date": day.isoformat(),
            "event_time": event_time, "guests": guests, "total_price": total, "ticket_code": code,
        },
    }


def get_bookings_by_customer(customer_email):
    """All bookings of one customer. 'status' is what the customer sees:
    Confirmed, Checked in, Expired or Cancelled."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT b.id, b.event_id, b.event_title, b.venue_name, b.booking_date, b.event_time, b.guests, "
            "b.total_price, b.ticket_code, b.status, t.status "
            "FROM bookings b LEFT JOIN tickets t ON t.ticket_code = b.ticket_code "
            "WHERE lower(b.customer_email) = lower(?) ORDER BY b.booking_date, b.id",
            ((customer_email or "").strip(),),
        ).fetchall()

    today = date.today().isoformat()
    bookings = []
    for r in rows:
        booking_status, ticket_status = r[9], r[10]
        if booking_status == "Cancelled" or ticket_status == "Cancelled":
            shown = "Cancelled"
        elif ticket_status == "Used":
            shown = "Checked in"
        elif r[4] < today:
            shown = "Expired"
        else:
            shown = "Confirmed"
        bookings.append({
            "id": r[0], "event_id": r[1], "event_title": r[2], "venue_name": r[3], "booking_date": r[4],
            "event_time": r[5], "guests": r[6], "total_price": r[7], "ticket_code": r[8],
            "status": shown, "can_cancel": shown == "Confirmed",
        })
    return bookings


def cancel_booking(booking_id, customer_email):
    """Cancels a booking and its ticket. Returns {"success": bool, "message": str}."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT ticket_code, booking_date, status FROM bookings WHERE id = ? AND lower(customer_email) = lower(?)",
            (booking_id, (customer_email or "").strip()),
        ).fetchone()
        if not row:
            return {"success": False, "message": "Booking not found."}
        code, day, status = row
        if status != "Confirmed":
            return {"success": False, "message": "This booking is already cancelled."}
        if day < date.today().isoformat():
            return {"success": False, "message": "Past bookings cannot be cancelled."}
        updated = conn.execute(
            "UPDATE tickets SET status = 'Cancelled' WHERE ticket_code = ? AND status = 'Valid'", (code,)
        ).rowcount
        if not updated:
            return {"success": False, "message": "This ticket was already used, so the booking cannot be cancelled."}
        conn.execute("UPDATE bookings SET status = 'Cancelled' WHERE id = ?", (booking_id,))
    return {"success": True, "message": "Booking cancelled. The ticket code no longer works."}


def count_active_bookings(event_id):
    """Bookings that will be cancelled if the event is deleted (unused tickets only)."""
    with _connect() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM bookings b JOIN tickets t ON t.ticket_code = b.ticket_code "
            "WHERE b.event_id = ? AND b.status = 'Confirmed' AND t.status = 'Valid'",
            (event_id,),
        ).fetchone()[0]


def _shown_status(booking_status, ticket_status, booking_date):
    if booking_status == "Cancelled" or ticket_status == "Cancelled":
        return "Cancelled"
    if ticket_status == "Used":
        return "Checked in"
    if booking_date < date.today().isoformat():
        return "Expired"
    return "Confirmed"


def get_bookings_by_vendor(vendor_email):
    """Bookings made for the events of one vendor, newest date first."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT b.id, b.event_title, b.venue_name, b.booking_date, b.event_time, b.guests, b.total_price, "
            "b.customer_email, b.status, t.status "
            "FROM bookings b JOIN events e ON e.id = b.event_id LEFT JOIN tickets t ON t.ticket_code = b.ticket_code "
            "WHERE lower(e.vendor_email) = lower(?) ORDER BY b.booking_date DESC, b.id DESC",
            ((vendor_email or "").strip(),),
        ).fetchall()
    return [{
        "id": r[0], "event_title": r[1], "venue_name": r[2], "booking_date": r[3], "event_time": r[4],
        "guests": r[5], "total_price": r[6], "customer_email": r[7], "status": _shown_status(r[8], r[9], r[3]),
    } for r in rows]


def get_event_demand(event_id):
    """(bookings, guests) still to come for one event. Cancelled bookings are not counted."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(guests), 0) FROM bookings "
            "WHERE event_id = ? AND status = 'Confirmed' AND booking_date >= ?",
            (event_id, date.today().isoformat()),
        ).fetchone()
    return row[0], row[1]


def get_events_today():
    """Events that run today, with how many guests are booked and how many were checked in."""
    today = date.today()
    result = []
    for e in get_all_events():
        if not _event_allows_date(e["is_recurring"], e["recur_day"], e["event_datetime"], today):
            continue
        with _connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(b.guests), 0), "
                "COALESCE(SUM(CASE WHEN t.status = 'Used' THEN b.guests ELSE 0 END), 0) "
                "FROM bookings b LEFT JOIN tickets t ON t.ticket_code = b.ticket_code "
                "WHERE b.event_id = ? AND b.booking_date = ? AND b.status = 'Confirmed'",
                (e["id"], today.isoformat()),
            ).fetchone()
        result.append({
            "id": e["id"], "title": e["title"], "venue_name": e["venue_name"],
            "time": e["recur_time"] or str(e["event_datetime"] or "")[11:16],
            "bookings": row[0], "guests": row[1], "checked_in": row[2],
        })
    result.sort(key=lambda item: item["time"] or "")
    return result


# ---------------------------------------------------------------- support tickets
MAX_OPEN_SUPPORT_TICKETS = 5


def create_support_ticket(customer_email, subject, message):
    customer_email = (customer_email or "").strip()
    subject = (subject or "").strip()
    message = (message or "").strip()
    if not customer_email:
        return {"success": False, "message": "You must be logged in."}
    if not 3 <= len(subject) <= 100:
        return {"success": False, "message": "The subject must be 3 to 100 characters."}
    if not 10 <= len(message) <= 2000:
        return {"success": False, "message": "The message must be 10 to 2000 characters."}
    with _connect() as conn:
        open_count = conn.execute(
            "SELECT COUNT(*) FROM support_tickets WHERE lower(customer_email) = lower(?) AND status = 'Open'",
            (customer_email,),
        ).fetchone()[0]
        if open_count >= MAX_OPEN_SUPPORT_TICKETS:
            return {"success": False, "message": "You already have several open tickets. Please wait for a reply."}
        conn.execute(
            "INSERT INTO support_tickets (customer_email, subject, message) VALUES (?, ?, ?)",
            (customer_email, subject, message),
        )
    return {"success": True, "message": "Your message was sent to our staff."}


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