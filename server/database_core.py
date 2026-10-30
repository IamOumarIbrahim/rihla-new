import hashlib
import hmac
from datetime import date, datetime
import os
import re
import secrets
import sqlite3
from contextlib import contextmanager

from config import DEMO_ACCOUNTS, ADMIN_ROLE, SIGNUP_ROLES

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")
# Server-side: DB always lives next to this file (server/users.db)

# Guests an event can take on one date when no vehicles are assigned to it.
DEFAULT_EVENT_CAPACITY = 20
MAX_EVENT_CAPACITY = 5000
MAX_GUESTS_PER_BOOKING = 10
MAX_OPEN_SUPPORT_TICKETS = 3

CURRENCIES = ("AED", "USD", "EUR", "GBP")
DEFAULT_CURRENCY = "AED"


SSN_LENGTH = 16
# Made-up SSNs for the non-customer demo accounts, so they follow the same rule as real sign-ups.
DEMO_SSNS = {
    "Vendor": "4000100020003001",
    "Staff": "4000100020003002",
    "Partner": "4000100020003003",
    "Dispatcher": "4000100020003004",
    "Admin": "4000100020003005",
}


def clean_ssn(ssn):
    """Drops spaces and dashes: '1234 5678-...' -> '12345678...'."""
    return "".join(c for c in str(ssn or "") if c not in " -")


def ssn_error(role, ssn):
    """None when the SSN is fine for this role, otherwise the message to show. Customers need no SSN."""
    if role == "Customer":
        return None
    ssn = clean_ssn(ssn)
    if not ssn:
        return f"A {SSN_LENGTH}-digit SSN is required for {role} accounts."
    if len(ssn) != SSN_LENGTH or not (ssn.isascii() and ssn.isdigit()):
        return f"The SSN must be exactly {SSN_LENGTH} digits (0-9)."
    if len(set(ssn)) == 1:
        return "Please enter your real SSN."
    return None


STAFF_ROLE = "Staff"
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# The demo staff account works at the venue of the demo ticket (New year dinner).
DEMO_STAFF_VENUE = "Burj Khalifa"


def default_manager_email(venue_name):
    """Made-up manager address for a venue: 'Burj Khalifa' -> 'manager.burjkhalifa@email.com'."""
    slug = "".join(c for c in (venue_name or "").lower() if c.isascii() and c.isalnum()) or "venue"
    return f"manager.{slug}@email.com"


def staff_venue_error(venue_id, manager_email, conn=None):
    """None when the venue exists and the manager email looks like an email, otherwise the message to show."""
    try:
        venue_id = int(venue_id)
    except (TypeError, ValueError):
        return "Please choose the venue you work at."
    if conn is None:
        with _connect() as conn:
            exists = conn.execute("SELECT 1 FROM venues WHERE id = ?", (venue_id,)).fetchone()
    else:
        exists = conn.execute("SELECT 1 FROM venues WHERE id = ?", (venue_id,)).fetchone()
    if not exists:
        return "That venue does not exist. Please choose one from the list."
    manager_email = (manager_email or "").strip()
    if not manager_email:
        return "Please enter your venue manager's email."
    if not _EMAIL_RE.match(manager_email):
        return "The manager email is not a valid email address."
    return None


def _now():
    """Server's local time, in the same text form SQLite timestamps use."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


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
                phone TEXT,
                created_at TEXT,
                banned INTEGER NOT NULL DEFAULT 0,
                banned_at TEXT,
                banned_by TEXT
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
                cancelled_at TEXT,
                cancelled_by TEXT,
                cancelled_by_role TEXT,
                cancel_reason TEXT NOT NULL DEFAULT '',
                refund_percent INTEGER,
                refund_amount REAL,
                FOREIGN KEY(event_id) REFERENCES events(id)
            )
        ''')
        conn.execute("CREATE INDEX IF NOT EXISTS idx_bookings_customer ON bookings(customer_email)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_bookings_event ON bookings(event_id, booking_date)")

        conn.execute('''
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_email TEXT NOT NULL,
                event_title TEXT NOT NULL DEFAULT '',
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Open',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                resolved_by TEXT,
                resolved_at TEXT
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_email TEXT NOT NULL,
                reporter_role TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL,
                offender_type TEXT NOT NULL,
                offender_email TEXT NOT NULL DEFAULT '',
                subject TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Open',
                created_at TEXT,
                resolved_by TEXT,
                resolved_at TEXT,
                resolution TEXT NOT NULL DEFAULT ''
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

        # Venues made before map links existed get the new column (old venues start without a link).
        venue_columns = [row[1] for row in conn.execute("PRAGMA table_info(venues)")]
        if "maps_url" not in venue_columns:
            conn.execute("ALTER TABLE venues ADD COLUMN maps_url TEXT NOT NULL DEFAULT ''")

        # Support tickets made before tickets had to name an event start without one.
        support_columns = [row[1] for row in conn.execute("PRAGMA table_info(support_tickets)")]
        if "event_title" not in support_columns:
            conn.execute("ALTER TABLE support_tickets ADD COLUMN event_title TEXT NOT NULL DEFAULT ''")

        # Check bookings table for client_name column
        # Users made before currency preferences existed default to AED.
        user_columns = [row[1] for row in conn.execute("PRAGMA table_info(users)")]
        if "currency" not in user_columns:
            conn.execute(f"ALTER TABLE users ADD COLUMN currency TEXT NOT NULL DEFAULT '{DEFAULT_CURRENCY}'")
        # Users made before sign-up dates and bans existed: the date is backfilled below, nobody starts banned.
        if "created_at" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN created_at TEXT")
        if "banned" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN banned INTEGER NOT NULL DEFAULT 0")
            conn.execute("ALTER TABLE users ADD COLUMN banned_at TEXT")
            conn.execute("ALTER TABLE users ADD COLUMN banned_by TEXT")
        # Non-customer accounts give a 16-digit SSN: only a salted hash and the last 4 digits are kept.
        if "ssn_hash" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN ssn_hash TEXT")
            conn.execute("ALTER TABLE users ADD COLUMN ssn_last4 TEXT")
        # Staff work at one venue and name its manager; staff made before this get one below.
        if "venue_id" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN venue_id INTEGER REFERENCES venues(id)")
            conn.execute("ALTER TABLE users ADD COLUMN manager_email TEXT")

        booking_columns = [row[1] for row in conn.execute("PRAGMA table_info(bookings)")]
        if "client_name" not in booking_columns:
            conn.execute("ALTER TABLE bookings ADD COLUMN client_name TEXT DEFAULT ''")
        # Cancellation audit trail and refund (older databases get the columns here)
        if "cancelled_at" not in booking_columns:
            conn.execute("ALTER TABLE bookings ADD COLUMN cancelled_at TEXT")
            conn.execute("ALTER TABLE bookings ADD COLUMN cancelled_by TEXT")
            conn.execute("ALTER TABLE bookings ADD COLUMN cancelled_by_role TEXT")
            conn.execute("ALTER TABLE bookings ADD COLUMN cancel_reason TEXT NOT NULL DEFAULT ''")
            conn.execute("ALTER TABLE bookings ADD COLUMN refund_percent INTEGER")
            conn.execute("ALTER TABLE bookings ADD COLUMN refund_amount REAL")

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
                    "INSERT INTO users (email, password, role, phone, created_at) VALUES (?, ?, ?, ?, ?)",
                    (demo_email, hash_password(demo_password), demo_role, None, _now()),
                )
            demo_ssn = DEMO_SSNS.get(demo_role)
            if demo_ssn:
                conn.execute(
                    "UPDATE users SET ssn_hash = ?, ssn_last4 = ? WHERE lower(email) = ? AND ssn_hash IS NULL",
                    (hash_password(demo_ssn), demo_ssn[-4:], demo_email.lower()),
                )

        # Accounts without a sign-up date (made before it was recorded): use their first booking or
        # support ticket, the earliest sign of the account we have, otherwise the time of this upgrade.
        undated = conn.execute("SELECT rowid, email FROM users WHERE created_at IS NULL OR created_at = ''").fetchall()
        for rowid, user_email in undated:
            first_seen = conn.execute(
                "SELECT MIN(t) FROM ("
                "SELECT created_at AS t FROM bookings WHERE lower(customer_email) = lower(?) "
                "UNION ALL SELECT created_at FROM support_tickets WHERE lower(customer_email) = lower(?))",
                (user_email, user_email),
            ).fetchone()[0]
            conn.execute("UPDATE users SET created_at = ? WHERE rowid = ?", (first_seen or _now(), rowid))

        # Staff without a venue (made before venues were assigned, or whose venue was deleted): the demo
        # staff account goes to the demo ticket's venue, anyone else to the first venue; the manager email
        # is a made-up address for that venue until they change it in Settings.
        venues = conn.execute("SELECT id, name FROM venues ORDER BY id").fetchall()
        if venues:
            demo_venue = next((v for v in venues if v[1] == DEMO_STAFF_VENUE), venues[0])
            demo_staff_email = DEMO_ACCOUNTS[STAFF_ROLE][0].lower()
            unassigned = conn.execute(
                "SELECT rowid, lower(email) FROM users WHERE role = ? AND "
                "(venue_id IS NULL OR venue_id NOT IN (SELECT id FROM venues))", (STAFF_ROLE,)
            ).fetchall()
            for rowid, user_email in unassigned:
                venue = demo_venue if user_email == demo_staff_email else venues[0]
                conn.execute("UPDATE users SET venue_id = ? WHERE rowid = ?", (venue[0], rowid))
            names = dict(venues)
            for rowid, venue_id in conn.execute(
                "SELECT rowid, venue_id FROM users WHERE role = ? AND (manager_email IS NULL OR manager_email = '')",
                (STAFF_ROLE,),
            ).fetchall():
                conn.execute("UPDATE users SET manager_email = ? WHERE rowid = ?",
                             (default_manager_email(names.get(venue_id)), rowid))


def register_user(email, password, role="Customer", phone=None, ssn=None, venue_id=None, manager_email=None):
    if role not in SIGNUP_ROLES:
        role = "Customer"
    email = (email or "").strip().lower()
    if not email or not password or email_exists(email) or ssn_error(role, ssn):
        return False
    if role == STAFF_ROLE:
        if staff_venue_error(venue_id, manager_email):
            return False
        venue_id, manager_email = int(venue_id), manager_email.strip()
    else:
        venue_id, manager_email = None, None
    ssn = clean_ssn(ssn) if role != "Customer" else ""
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO users (email, password, role, phone, created_at, ssn_hash, ssn_last4, venue_id, manager_email) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (email, hash_password(password), role, phone, _now(),
                 hash_password(ssn) if ssn else None, ssn[-4:] if ssn else None, venue_id, manager_email),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def get_staff_venue(email):
    """The venue a (not banned) staff account works at, with its manager email, or None."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT v.id, v.name, v.address, v.maps_url, u.manager_email FROM users u JOIN venues v ON v.id = u.venue_id "
            "WHERE lower(u.email) = lower(?) AND u.role = ? AND u.banned = 0",
            ((email or "").strip(), STAFF_ROLE),
        ).fetchone()
    if row is None:
        return None
    return {"id": row[0], "name": row[1], "address": row[2], "maps_url": row[3] or "", "manager_email": row[4] or ""}


def set_staff_venue(email, venue_id, manager_email):
    """A staff member moves to another venue and/or names a new manager. Returns {"success", "message"}."""
    email = (email or "").strip()
    with _connect() as conn:
        row = conn.execute("SELECT role, banned FROM users WHERE lower(email) = lower(?)", (email,)).fetchone()
        if row is None or row[0] != STAFF_ROLE or row[1]:
            return {"success": False, "message": "Only staff accounts work at a venue."}
        problem = staff_venue_error(venue_id, manager_email, conn)
        if problem:
            return {"success": False, "message": problem}
        conn.execute("UPDATE users SET venue_id = ?, manager_email = ? WHERE lower(email) = lower(?)",
                     (int(venue_id), manager_email.strip(), email))
    return {"success": True, "message": "Your venue and manager email were saved."}


def login_status(email, password):
    """'ok', 'invalid' (unknown email or wrong password) or 'banned' (right password, banned account)."""
    email = (email or "").strip()
    with _connect() as conn:
        row = conn.execute(
            "SELECT email, password, banned FROM users WHERE lower(email) = lower(?)", (email,)
        ).fetchone()
        if row is None or not verify_password(password, row[1]):
            return "invalid"
        if not row[1].startswith(_HASH_PREFIX):
            # Upgrade an old plain-text password to a salted hash after a successful login.
            conn.execute("UPDATE users SET password = ? WHERE email = ?", (hash_password(password), row[0]))
        if row[2]:
            return "banned"
    return "ok"


def check_login(email, password):
    return login_status(email, password) == "ok"


def is_admin(email):
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE lower(email) = lower(?) AND role = ? AND banned = 0",
            ((email or "").strip(), ADMIN_ROLE),
        ).fetchone()
    return row is not None


def get_all_users(admin_email):
    """Every account, newest sign-up first. Only an admin may list them (None otherwise)."""
    if not is_admin(admin_email):
        return None
    with _connect() as conn:
        rows = conn.execute(
            "SELECT u.email, u.role, u.created_at, u.banned, u.banned_at, u.banned_by, v.name, u.manager_email "
            "FROM users u LEFT JOIN venues v ON v.id = u.venue_id "
            "ORDER BY u.created_at DESC, lower(u.email)"
        ).fetchall()
    # Venue and manager email only mean something for staff; everyone else gets blanks.
    return [{"email": r[0], "role": r[1] or "Customer", "created_at": r[2] or "", "banned": bool(r[3]),
             "banned_at": r[4] or "", "banned_by": r[5] or "",
             "venue_name": (r[6] or "") if r[1] == STAFF_ROLE else "",
             "manager_email": (r[7] or "") if r[1] == STAFF_ROLE else ""} for r in rows]


def set_user_banned(admin_email, email, banned=True):
    """Ban (or restore) an account. Admins cannot ban themselves or another admin."""
    admin_email = (admin_email or "").strip()
    email = (email or "").strip()
    if not is_admin(admin_email):
        return {"success": False, "message": "Only an admin can do this."}
    if email.lower() == admin_email.lower():
        return {"success": False, "message": "You cannot ban your own account."}
    with _connect() as conn:
        row = conn.execute("SELECT role FROM users WHERE lower(email) = lower(?)", (email,)).fetchone()
        if row is None:
            return {"success": False, "message": "No account with that email."}
        if row[0] == ADMIN_ROLE:
            return {"success": False, "message": "Admin accounts cannot be banned."}
        if banned:
            conn.execute("UPDATE users SET banned = 1, banned_at = ?, banned_by = ? WHERE lower(email) = lower(?)",
                         (_now(), admin_email, email))
        else:
            conn.execute("UPDATE users SET banned = 0, banned_at = NULL, banned_by = NULL WHERE lower(email) = lower(?)",
                         (email,))
    return {"success": True, "message": f"{email} was {'banned' if banned else 'restored'}."}


def get_user_email(email):
    """Returns the email exactly as stored (the typed letter case does not matter), or None."""
    with _connect() as conn:
        row = conn.execute("SELECT email FROM users WHERE lower(email) = lower(?)", ((email or "").strip(),)).fetchone()
    return row[0] if row else None


def get_role(email):
    with _connect() as conn:
        row = conn.execute("SELECT role FROM users WHERE lower(email) = lower(?)", ((email or "").strip(),)).fetchone()
    return row[0] if row and row[0] else "Customer"


def get_currency(email):
    with _connect() as conn:
        row = conn.execute("SELECT currency FROM users WHERE lower(email) = lower(?)", ((email or "").strip(),)).fetchone()
    return row[0] if row and row[0] in CURRENCIES else DEFAULT_CURRENCY


def set_currency(email, currency):
    currency = (currency or "").strip().upper()
    if currency not in CURRENCIES:
        return False
    with _connect() as conn:
        cursor = conn.execute("UPDATE users SET currency = ? WHERE lower(email) = lower(?)", (currency, (email or "").strip()))
    return cursor.rowcount > 0


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
def create_support_ticket(customer_email, subject, message, event_title=""):
    """The ticket must be about an event: one that is listed now, or one the customer has booked before."""
    customer_email = (customer_email or "").strip()
    subject = (subject or "").strip()
    message = (message or "").strip()
    event_title = (event_title or "").strip()

    if not event_title:
        return {"success": False, "message": "Please choose the event your message is about."}
    if not subject or not message:
        return {"success": False, "message": "Subject and message are required."}
    if len(subject) < 3:
        return {"success": False, "message": "Subject must be at least 3 characters."}
    if len(message) < 10:
        return {"success": False, "message": "Message must be at least 10 characters."}

    with _connect() as conn:
        listed = conn.execute("SELECT 1 FROM events WHERE lower(title) = lower(?)", (event_title,)).fetchone()
        booked = conn.execute(
            "SELECT 1 FROM bookings WHERE lower(customer_email) = lower(?) AND lower(event_title) = lower(?)",
            (customer_email, event_title),
        ).fetchone()
        if not listed and not booked:
            return {"success": False, "message": "Please choose an event from the list."}

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
            "INSERT INTO support_tickets (customer_email, event_title, subject, message, status) VALUES (?, ?, ?, ?, 'Open')",
            (customer_email, event_title, subject, message),
        )
        ticket_id = cursor.lastrowid
    return {"success": True, "message": "Support ticket created.", "ticket_id": ticket_id}


def get_support_tickets_by_customer(customer_email):
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, subject, message, status, created_at, event_title FROM support_tickets "
            "WHERE lower(customer_email) = lower(?) ORDER BY id DESC",
            ((customer_email or "").strip(),),
        ).fetchall()
    return [{"id": r[0], "subject": r[1], "message": r[2], "status": r[3], "created_at": r[4], "event_title": r[5] or ""} for r in rows]


# A support ticket belongs to the venue of the event it names. An event that has since been deleted is
# found through its bookings (they keep the venue name). Old tickets that name no event are general
# questions any staff member may answer.
_TICKET_AT_VENUE = (
    "(t.event_title = '' OR t.event_title IS NULL "
    "OR EXISTS (SELECT 1 FROM events e WHERE e.title = t.event_title AND e.venue_id = :venue) "
    "OR (NOT EXISTS (SELECT 1 FROM events e WHERE e.title = t.event_title) "
    "AND EXISTS (SELECT 1 FROM bookings b JOIN venues v ON v.name = b.venue_name "
    "WHERE b.event_title = t.event_title AND v.id = :venue)))"
)


def _staff_venue_id(staff_email):
    with _connect() as conn:
        row = conn.execute(
            "SELECT venue_id FROM users WHERE lower(email) = lower(?) AND role = ? AND banned = 0 AND venue_id IS NOT NULL",
            ((staff_email or "").strip(), STAFF_ROLE),
        ).fetchone()
    return row[0] if row else None


def get_open_support_tickets(venue_id=None):
    """Oldest first, so the longest waiting customer is answered first. venue_id keeps that venue's tickets."""
    where = "t.status = 'Open'" + ("" if venue_id is None else f" AND {_TICKET_AT_VENUE}")
    with _connect() as conn:
        rows = conn.execute(
            "SELECT t.id, t.customer_email, t.subject, t.message, t.created_at, t.event_title FROM support_tickets t "
            f"WHERE {where} ORDER BY t.id", {"venue": venue_id}
        ).fetchall()
    return [{"id": r[0], "customer_email": r[1], "subject": r[2], "message": r[3], "created_at": r[4], "event_title": r[5] or ""} for r in rows]


def resolve_support_ticket(ticket_id, staff_email, venue_id=None):
    """venue_id: only a ticket for that venue can be resolved."""
    where = "id = :id AND status = 'Open'"
    if venue_id is not None:
        where += f" AND id IN (SELECT t.id FROM support_tickets t WHERE {_TICKET_AT_VENUE})"
    with _connect() as conn:
        updated = conn.execute(
            f"UPDATE support_tickets SET status = 'Resolved', resolved_by = :staff, resolved_at = CURRENT_TIMESTAMP WHERE {where}",
            {"staff": (staff_email or "").strip(), "id": ticket_id, "venue": venue_id},
        ).rowcount
    return bool(updated)


def get_staff_support_tickets(staff_email):
    """Open support tickets for the staff member's venue, or None if they are not staff at a venue."""
    venue_id = _staff_venue_id(staff_email)
    return None if venue_id is None else get_open_support_tickets(venue_id)


def staff_resolve_support_ticket(ticket_id, staff_email):
    """Staff resolve only tickets about their own venue's events."""
    venue_id = _staff_venue_id(staff_email)
    return venue_id is not None and resolve_support_ticket(ticket_id, staff_email, venue_id)


# --- Reports (any signed-in user except admins files one, admins resolve them) ---
MAX_OPEN_REPORTS = 5


def create_report(reporter_email, category, offender_type, subject, description, offender_email=""):
    reporter_email = (reporter_email or "").strip()
    category = (category or "").strip()
    offender_type = (offender_type or "").strip()
    subject = (subject or "").strip()
    description = (description or "").strip()
    offender_email = (offender_email or "").strip()

    if not category or not offender_type:
        return {"success": False, "message": "Please choose what you are reporting and who it is about."}
    if len(subject) < 3:
        return {"success": False, "message": "Summary must be at least 3 characters."}
    if len(description) < 10:
        return {"success": False, "message": "Please describe what happened (at least 10 characters)."}

    with _connect() as conn:
        reporter = conn.execute("SELECT email, role, banned FROM users WHERE lower(email) = lower(?)", (reporter_email,)).fetchone()
        if reporter is None or reporter[2]:
            return {"success": False, "message": "Unknown account."}
        if reporter[1] == ADMIN_ROLE:
            return {"success": False, "message": "Admins handle reports instead of filing them."}
        if offender_email and offender_email.lower() == reporter[0].lower():
            return {"success": False, "message": "You cannot report your own account."}
        open_count = conn.execute(
            "SELECT COUNT(*) FROM reports WHERE lower(reporter_email) = lower(?) AND status = 'Open'", (reporter_email,)
        ).fetchone()[0]
        if open_count >= MAX_OPEN_REPORTS:
            return {"success": False, "message": f"You already have {MAX_OPEN_REPORTS} open reports. Please wait for an admin to review them."}
        cursor = conn.execute(
            "INSERT INTO reports (reporter_email, reporter_role, category, offender_type, offender_email, subject, description, "
            "status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'Open', ?)",
            (reporter[0], reporter[1] or "Customer", category, offender_type, offender_email, subject, description, _now()),
        )
    return {"success": True, "message": "Report sent to the admin team.", "report_id": cursor.lastrowid}


_REPORT_FIELDS = ("id", "reporter_email", "reporter_role", "category", "offender_type", "offender_email", "subject",
                  "description", "status", "created_at", "resolved_by", "resolved_at", "resolution")


def get_reports(admin_email):
    """All reports: open ones first (oldest first, so the longest waiting is handled first), then resolved ones."""
    if not is_admin(admin_email):
        return None
    with _connect() as conn:
        rows = conn.execute(
            f"SELECT {', '.join(_REPORT_FIELDS)} FROM reports "
            "ORDER BY status = 'Resolved', CASE WHEN status = 'Open' THEN id ELSE -id END"
        ).fetchall()
    return [{k: (v if v is not None else "") for k, v in zip(_REPORT_FIELDS, r)} for r in rows]


def resolve_report(admin_email, report_id, resolution="Resolved"):
    if not is_admin(admin_email):
        return {"success": False, "message": "Only an admin can do this."}
    with _connect() as conn:
        updated = conn.execute(
            "UPDATE reports SET status = 'Resolved', resolved_by = ?, resolved_at = ?, resolution = ? "
            "WHERE id = ? AND status = 'Open'",
            ((admin_email or "").strip(), _now(), (resolution or "Resolved").strip(), report_id),
        ).rowcount
    if not updated:
        return {"success": False, "message": "That report is already resolved or no longer exists."}
    return {"success": True, "message": "Report resolved."}
