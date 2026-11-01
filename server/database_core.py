import hashlib
import hmac
from datetime import datetime
import os
import re
import secrets
import sqlite3
from contextlib import contextmanager

from config import DEMO_ACCOUNTS, ADMIN_ROLE, SIGNUP_ROLES

# the db file is always next to this file (server/users.db)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")

# guests an event can take on one date when it has no vehicles
DEFAULT_EVENT_CAPACITY = 20
MAX_EVENT_CAPACITY = 5000
MAX_GUESTS_PER_BOOKING = 10
MAX_OPEN_SUPPORT_TICKETS = 3

CURRENCIES = ("AED", "USD", "EUR", "GBP")
DEFAULT_CURRENCY = "AED"


SSN_LENGTH = 16
# fake SSNs for the demo accounts that are not customers so they follow the same rule
DEMO_SSNS = {
    "Vendor": "4000100020003001",
    "Staff": "4000100020003002",
    "Partner": "4000100020003003",
    "Dispatcher": "4000100020003004",
    "Admin": "4000100020003005",
}


# removes spaces and dashes from the ssn
def clean_ssn(ssn):
    if not ssn:
        text = ""
    else:
        text = str(ssn)
    result = ""
    for c in text:
        if c != " " and c != "-":
            result = result + c
    return result


# returns None if the ssn is ok for the role, otherwise the error message
# customers dont need one
def ssn_error(role, ssn):
    if role == "Customer":
        return None
    ssn = clean_ssn(ssn)
    if not ssn:
        return "A " + str(SSN_LENGTH) + "-digit SSN is required for " + role + " accounts."
    if len(ssn) != SSN_LENGTH or not (ssn.isascii() and ssn.isdigit()):
        return "The SSN must be exactly " + str(SSN_LENGTH) + " digits (0-9)."

    # all the same digit like 1111... is not a real ssn
    same = True
    for c in ssn:
        if c != ssn[0]:
            same = False
    if same:
        return "Please enter your real SSN."
    return None


STAFF_ROLE = "Staff"
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# demo staff works at the venue of the demo ticket (New year dinner)
DEMO_STAFF_VENUE = "Burj Khalifa"


# fake manager email for a venue, Burj Khalifa -> manager.burjkhalifa@email.com
def default_manager_email(venue_name):
    if venue_name:
        name = venue_name.lower()
    else:
        name = ""
    slug = ""
    for c in name:
        if c.isascii() and c.isalnum():
            slug = slug + c
    if slug == "":
        slug = "venue"
    return "manager." + slug + "@email.com"


# None when the venue exists and the manager email is ok, otherwise the message
def staff_venue_error(venue_id, manager_email, conn=None):
    try:
        venue_id = int(venue_id)
    except (TypeError, ValueError):
        return "Please choose the venue you work at."
    if conn is None:
        with _connect() as conn:
            exsits = conn.execute("SELECT 1 FROM venues WHERE id = ?", (venue_id,)).fetchone()
    else:
        exsits = conn.execute("SELECT 1 FROM venues WHERE id = ?", (venue_id,)).fetchone()
    if not exsits:
        return "That venue does not exist. Please choose one from the list."
    if manager_email:
        manager_email = manager_email.strip()
    else:
        manager_email = ""
    if not manager_email:
        return "Please enter your venue manager's email."
    if not _EMAIL_RE.match(manager_email):
        return "The manager email is not a valid email address."
    return None


# local time of the server in the same format sqlite uses
def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# opens the server db, commits at the end and always closes it
@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


_HASH_PREFIX = "pbkdf2$"
_HASH_ROUNDS = 200000


# salted pbkdf2 hash so passwords are never saved as plain text
def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), _HASH_ROUNDS)
    return _HASH_PREFIX + str(_HASH_ROUNDS) + "$" + salt + "$" + digest.hex()


def verify_password(password, stored):
    if not stored:
        return False
    if not stored.startswith(_HASH_PREFIX):
        # old row from before hashing was added (plain text)
        return hmac.compare_digest(password.encode("utf-8"), stored.encode("utf-8"))
    try:
        prefix, rounds, salt, digest = stored.split("$")
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

        # Upgrading old databases:

        # old events from before capacity existed get the column (they start at 20)
        event_columns = []
        for row in conn.execute("PRAGMA table_info(events)"):
            event_columns.append(row[1])
        if "capacity" not in event_columns:
            conn.execute("ALTER TABLE events ADD COLUMN capacity INTEGER NOT NULL DEFAULT " + str(DEFAULT_EVENT_CAPACITY))

        # old venues dont have a map link
        venue_columns = []
        for row in conn.execute("PRAGMA table_info(venues)"):
            venue_columns.append(row[1])
        if "maps_url" not in venue_columns:
            conn.execute("ALTER TABLE venues ADD COLUMN maps_url TEXT NOT NULL DEFAULT ''")

        # old support tickets from before they had to name an event
        support_columns = []
        for row in conn.execute("PRAGMA table_info(support_tickets)"):
            support_columns.append(row[1])
        if "event_title" not in support_columns:
            conn.execute("ALTER TABLE support_tickets ADD COLUMN event_title TEXT NOT NULL DEFAULT ''")

        # old users get AED as currency
        user_columns = []
        for row in conn.execute("PRAGMA table_info(users)"):
            user_columns.append(row[1])
        if "currency" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN currency TEXT NOT NULL DEFAULT '" + DEFAULT_CURRENCY + "'")
        # sign up date gets filled in further down, nobody starts banned
        if "created_at" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN created_at TEXT")
        if "banned" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN banned INTEGER NOT NULL DEFAULT 0")
            conn.execute("ALTER TABLE users ADD COLUMN banned_at TEXT")
            conn.execute("ALTER TABLE users ADD COLUMN banned_by TEXT")
        # non customers give a 16 digit ssn, we only keep a salted hash and the last 4 digits
        if "ssn_hash" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN ssn_hash TEXT")
            conn.execute("ALTER TABLE users ADD COLUMN ssn_last4 TEXT")
        # staff work at one venue and have a manager
        if "venue_id" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN venue_id INTEGER REFERENCES venues(id)")
            conn.execute("ALTER TABLE users ADD COLUMN manager_email TEXT")

        booking_columns = []
        for row in conn.execute("PRAGMA table_info(bookings)"):
            booking_columns.append(row[1])
        if "client_name" not in booking_columns:
            conn.execute("ALTER TABLE bookings ADD COLUMN client_name TEXT DEFAULT ''")
        # cancel info and refund
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

        # Default data
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

        # link the demo ticket to a real booking so My Bookings shows something
        demo_code = "1234567890123456"
        demo_ticket = conn.execute("SELECT 1 FROM tickets WHERE ticket_code = ?", (demo_code,)).fetchone()
        demo_booked = conn.execute("SELECT 1 FROM bookings WHERE ticket_code = ?", (demo_code,)).fetchone()
        demo_event = conn.execute(
            "SELECT e.id, e.title, e.recur_time, v.name FROM events e LEFT JOIN venues v ON v.id = e.venue_id "
            "WHERE e.title = 'New year dinner'"
        ).fetchone()
        if demo_ticket and not demo_booked and demo_event:
            demo_time = demo_event[2]
            if not demo_time:
                demo_time = "23:00"
            conn.execute(
                "INSERT INTO bookings (customer_email, event_id, event_title, venue_name, booking_date, event_time, "
                "guests, total_price, ticket_code, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Confirmed')",
                ("customer@email.com", demo_event[0], demo_event[1], demo_event[3], "2026-12-31", demo_time, 2, 1000, demo_code),
            )

        # older versions saved a wrong address for the first venue
        conn.execute("UPDATE venues SET address = 'Dubai Downtown, Dubai' WHERE address = 'Dubai Downtown, Dubai, Sharjah'")

        # the demo accounts on the login screen have to really exist
        for demo_role in DEMO_ACCOUNTS:
            demo_email = DEMO_ACCOUNTS[demo_role][0]
            demo_password = DEMO_ACCOUNTS[demo_role][1]
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

        # accounts with no sign up date get the date of their first booking or support ticket
        # if there is none then just the time of this upgrade
        undated = conn.execute("SELECT rowid, email FROM users WHERE created_at IS NULL OR created_at = ''").fetchall()
        for rowid, user_email in undated:
            first_seen = conn.execute(
                "SELECT MIN(t) FROM ("
                "SELECT created_at AS t FROM bookings WHERE lower(customer_email) = lower(?) "
                "UNION ALL SELECT created_at FROM support_tickets WHERE lower(customer_email) = lower(?))",
                (user_email, user_email),
            ).fetchone()[0]
            if not first_seen:
                first_seen = _now()
            conn.execute("UPDATE users SET created_at = ? WHERE rowid = ?", (first_seen, rowid))

        # staff without a venue: the demo staff goes to the venue of the demo ticket and everyone
        # else to the first venue  the manager email is made up until they change it in Settings
        venues = conn.execute("SELECT id, name FROM venues ORDER BY id").fetchall()
        if venues:
            demo_venue = venues[0]
            for v in venues:
                if v[1] == DEMO_STAFF_VENUE:
                    demo_venue = v
                    break
            demo_staff_email = DEMO_ACCOUNTS[STAFF_ROLE][0].lower()
            unassigned = conn.execute(
                "SELECT rowid, lower(email) FROM users WHERE role = ? AND "
                "(venue_id IS NULL OR venue_id NOT IN (SELECT id FROM venues))", (STAFF_ROLE,)
            ).fetchall()
            for rowid, user_email in unassigned:
                if user_email == demo_staff_email:
                    venue = demo_venue
                else:
                    venue = venues[0]
                conn.execute("UPDATE users SET venue_id = ? WHERE rowid = ?", (venue[0], rowid))

            names = {}
            for v in venues:
                names[v[0]] = v[1]
            no_manager = conn.execute(
                "SELECT rowid, venue_id FROM users WHERE role = ? AND (manager_email IS NULL OR manager_email = '')",
                (STAFF_ROLE,),
            ).fetchall()
            for rowid, venue_id in no_manager:
                conn.execute("UPDATE users SET manager_email = ? WHERE rowid = ?",
                             (default_manager_email(names.get(venue_id)), rowid))


def register_user(email, password, role="Customer", phone=None, ssn=None, venue_id=None, manager_email=None):
    if role not in SIGNUP_ROLES:
        role = "Customer"
    if email:
        email = email.strip().lower()
    else:
        email = ""
    if not email or not password or email_exists(email) or ssn_error(role, ssn):
        return False
    if role == STAFF_ROLE:
        if staff_venue_error(venue_id, manager_email):
            return False
        venue_id = int(venue_id)
        manager_email = manager_email.strip()
    else:
        venue_id = None
        manager_email = None

    if role != "Customer":
        ssn = clean_ssn(ssn)
    else:
        ssn = ""
    ssn_hash = None
    last4 = None
    if ssn:
        ssn_hash = hash_password(ssn)
        last4 = ssn[-4:]

    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO users (email, password, role, phone, created_at, ssn_hash, ssn_last4, venue_id, manager_email) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (email, hash_password(password), role, phone, _now(), ssn_hash, last4, venue_id, manager_email),
            )
        return True
    except sqlite3.IntegrityError:
        return False


# the venue of a staff account (not banned) with the manager email, or None
def get_staff_venue(email):
    if email:
        email = email.strip()
    else:
        email = ""
    with _connect() as conn:
        row = conn.execute(
            "SELECT v.id, v.name, v.address, v.maps_url, u.manager_email FROM users u JOIN venues v ON v.id = u.venue_id "
            "WHERE lower(u.email) = lower(?) AND u.role = ? AND u.banned = 0",
            (email, STAFF_ROLE),
        ).fetchone()
    if row is None:
        return None
    maps_url = row[3]
    if not maps_url:
        maps_url = ""
    manager = row[4]
    if not manager:
        manager = ""
    return {"id": row[0], "name": row[1], "address": row[2], "maps_url": maps_url, "manager_email": manager}


# staff changes venue or manager email
def set_staff_venue(email, venue_id, manager_email):
    if email:
        email = email.strip()
    else:
        email = ""
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


# 'ok', 'invalid' (wrong email or password) or 'banned' (password right but account banned)
def login_status(email, password):
    if email:
        email = email.strip()
    else:
        email = ""
    with _connect() as conn:
        row = conn.execute(
            "SELECT email, password, banned FROM users WHERE lower(email) = lower(?)", (email,)
        ).fetchone()
        if row is None or not verify_password(password, row[1]):
            return "invalid"
        if not row[1].startswith(_HASH_PREFIX):
            # old plain text password, hash it now that the login worked
            conn.execute("UPDATE users SET password = ? WHERE email = ?", (hash_password(password), row[0]))
        if row[2]:
            return "banned"
    return "ok"


def check_login(email, password):
    return login_status(email, password) == "ok"


def is_admin(email):
    if email:
        email = email.strip()
    else:
        email = ""
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE lower(email) = lower(?) AND role = ? AND banned = 0",
            (email, ADMIN_ROLE),
        ).fetchone()
    return row is not None


# role of an account that exists and is not banned, otherwise None
def active_role(email):
    if email:
        email = email.strip()
    else:
        email = ""
    with _connect() as conn:
        row = conn.execute(
            "SELECT role FROM users WHERE lower(email) = lower(?) AND banned = 0", (email,)
        ).fetchone()
    if row is None:
        return None
    if row[0]:
        return row[0]
    return "Customer"


# all accounts newest first, only for admins (None if not admin)
def get_all_users(admin_email):
    if not is_admin(admin_email):
        return None
    with _connect() as conn:
        rows = conn.execute(
            "SELECT u.email, u.role, u.created_at, u.banned, u.banned_at, u.banned_by, v.name, u.manager_email "
            "FROM users u LEFT JOIN venues v ON v.id = u.venue_id "
            "ORDER BY u.created_at DESC, lower(u.email)"
        ).fetchall()

    users = []
    for r in rows:
        role = r[1]
        if not role:
            role = "Customer"
        # venue and manager only make sense for staff
        venue_name = ""
        manager = ""
        if r[1] == STAFF_ROLE:
            if r[6]:
                venue_name = r[6]
            if r[7]:
                manager = r[7]
        user = {}
        user["email"] = r[0]
        user["role"] = role
        user["created_at"] = r[2] or ""
        user["banned"] = bool(r[3])
        user["banned_at"] = r[4] or ""
        user["banned_by"] = r[5] or ""
        user["venue_name"] = venue_name
        user["manager_email"] = manager
        users.append(user)
    return users


# ban or unban an account, admins cant ban themselves or other admins
def set_user_banned(admin_email, email, banned=True):
    if admin_email:
        admin_email = admin_email.strip()
    else:
        admin_email = ""
    if email:
        email = email.strip()
    else:
        email = ""
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
    if banned:
        word = "banned"
    else:
        word = "restored"
    return {"success": True, "message": email + " was " + word + "."}


# gives back the email the way it is saved (letter case doesnt matter), or None
def get_user_email(email):
    if email:
        email = email.strip()
    else:
        email = ""
    with _connect() as conn:
        row = conn.execute("SELECT email FROM users WHERE lower(email) = lower(?)", (email,)).fetchone()
    if row:
        return row[0]
    return None


def get_role(email):
    if email:
        email = email.strip()
    else:
        email = ""
    with _connect() as conn:
        row = conn.execute("SELECT role FROM users WHERE lower(email) = lower(?)", (email,)).fetchone()
    if row and row[0]:
        return row[0]
    return "Customer"


def get_currency(email):
    if email:
        email = email.strip()
    else:
        email = ""
    with _connect() as conn:
        row = conn.execute("SELECT currency FROM users WHERE lower(email) = lower(?)", (email,)).fetchone()
    if row and row[0] in CURRENCIES:
        return row[0]
    return DEFAULT_CURRENCY


def set_currency(email, currency):
    if currency:
        currency = currency.strip().upper()
    else:
        currency = ""
    if currency not in CURRENCIES:
        return False
    if email:
        email = email.strip()
    else:
        email = ""
    with _connect() as conn:
        cursor = conn.execute("UPDATE users SET currency = ? WHERE lower(email) = lower(?)", (currency, email))
    return cursor.rowcount > 0


def update_password(email, new_password):
    if email:
        email = email.strip()
    else:
        email = ""
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET password = ? WHERE lower(email) = lower(?)",
            (hash_password(new_password), email),
        )


def email_exists(email):
    if email:
        email = email.strip()
    else:
        email = ""
    with _connect() as conn:
        row = conn.execute("SELECT 1 FROM users WHERE lower(email) = lower(?)", (email,)).fetchone()
    return row is not None


def phone_exists(phone):
    with _connect() as conn:
        row = conn.execute("SELECT 1 FROM users WHERE phone = ?", (phone,)).fetchone()
    return row is not None


# ====== Support Tickets ======

# the ticket has to be about an event that is listed now or one the customer booked before
def create_support_ticket(customer_email, subject, message, event_title=""):
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
                "message": "You already have " + str(MAX_OPEN_SUPPORT_TICKETS) + " open tickets. Please wait for staff to reply.",
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
    tickets = []
    for r in rows:
        tickets.append({"id": r[0], "subject": r[1], "message": r[2], "status": r[3], "created_at": r[4], "event_title": r[5] or ""})
    return tickets


# a support ticket belongs to the venue of its event  if the event was deleted we find the venue
# through the bookings (they keep the venue name)  old tickets with no event can be answered by any staff
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
    if row:
        return row[0]
    return None


# oldest first so whoever waited the longest gets an answer first
# with a venue_id only that venues tickets are returned
def get_open_support_tickets(venue_id=None):
    where = "t.status = 'Open'"
    if venue_id is not None:
        where = where + " AND " + _TICKET_AT_VENUE
    with _connect() as conn:
        rows = conn.execute(
            "SELECT t.id, t.customer_email, t.subject, t.message, t.created_at, t.event_title FROM support_tickets t "
            "WHERE " + where + " ORDER BY t.id", {"venue": venue_id}
        ).fetchall()
    tickets = []
    for r in rows:
        tickets.append({"id": r[0], "customer_email": r[1], "subject": r[2], "message": r[3], "created_at": r[4], "event_title": r[5] or ""})
    return tickets


# with a venue_id only a ticket of that venue can be resolved
def resolve_support_ticket(ticket_id, staff_email, venue_id=None):
    where = "id = :id AND status = 'Open'"
    if venue_id is not None:
        where = where + " AND id IN (SELECT t.id FROM support_tickets t WHERE " + _TICKET_AT_VENUE + ")"
    with _connect() as conn:
        updated = conn.execute(
            "UPDATE support_tickets SET status = 'Resolved', resolved_by = :staff, resolved_at = CURRENT_TIMESTAMP WHERE " + where,
            {"staff": (staff_email or "").strip(), "id": ticket_id, "venue": venue_id},
        ).rowcount
    return bool(updated)


# open tickets for the venue of this staff member, None if they arent staff at a venue
def get_staff_support_tickets(staff_email):
    venue_id = _staff_venue_id(staff_email)
    if venue_id is None:
        return None
    return get_open_support_tickets(venue_id)


# staff can only resolve tickets about events at their own venue
def staff_resolve_support_ticket(ticket_id, staff_email):
    venue_id = _staff_venue_id(staff_email)
    if venue_id is None:
        return False
    return resolve_support_ticket(ticket_id, staff_email, venue_id)


# ====== Reports ======
# any signed in user except admins can send one, admins resolve them
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
            return {"success": False, "message": "You already have " + str(MAX_OPEN_REPORTS) + " open reports. Please wait for an admin to review them."}
        reporter_role = reporter[1]
        if not reporter_role:
            reporter_role = "Customer"
        cursor = conn.execute(
            "INSERT INTO reports (reporter_email, reporter_role, category, offender_type, offender_email, subject, description, "
            "status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'Open', ?)",
            (reporter[0], reporter_role, category, offender_type, offender_email, subject, description, _now()),
        )
    return {"success": True, "message": "Report sent to the admin team.", "report_id": cursor.lastrowid}


_REPORT_FIELDS = ("id", "reporter_email", "reporter_role", "category", "offender_type", "offender_email", "subject",
                  "description", "status", "created_at", "resolved_by", "resolved_at", "resolution")


# all reports, the open ones first (oldest first) and then the resolved ones
def get_reports(admin_email):
    if not is_admin(admin_email):
        return None
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, reporter_email, reporter_role, category, offender_type, offender_email, subject, "
            "description, status, created_at, resolved_by, resolved_at, resolution FROM reports "
            "ORDER BY status = 'Resolved', CASE WHEN status = 'Open' THEN id ELSE -id END"
        ).fetchall()
    reports = []
    for r in rows:
        report = {}
        for i in range(len(_REPORT_FIELDS)):
            if r[i] is not None:
                report[_REPORT_FIELDS[i]] = r[i]
            else:
                report[_REPORT_FIELDS[i]] = ""
        reports.append(report)
    return reports


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
