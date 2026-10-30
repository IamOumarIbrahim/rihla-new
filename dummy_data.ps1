<#
.SYNOPSIS
    Fills the server database (server\users.db) with demo data: venues, events with pictures,
    vehicles and dispatches, extra customers (with sign-up dates), bookings (upcoming, today, past,
    cancelled), reviews, support tickets, reports for the admin and a partner cart.

.DESCRIPTION
    Run this from the project root folder (the one that contains src and server).

    Safe to run more than once: every row the script adds is recorded in a small "demo_seed"
    table, and each run first removes what the previous run added (plus any bookings, reviews
    and cart items that point at those seeded events), then seeds again.
    The demo accounts on the login screen (server\config.py) and anything you created yourself
    are never touched.

    Dates are relative to today, so the demo always has upcoming events, events happening
    today (for staff check-in) and past experiences (for reviews).
    Prices follow the app rules: stored in AED, booking totals include 5% VAT.
    Event pictures come from assets\event_pictures_dummy and are saved as
    server\event_images\<event id>.jpg (needs Pillow: python -m pip install pillow).

    Extra demo customers, and the extra staff, partner and dispatcher accounts, use the password  demo1234
    (non-customer accounts are seeded with a valid 16-digit SSN, as sign-up now requires)

.PARAMETER Clear
    Only remove the seeded data, do not seed again.

.EXAMPLE
    .\dummy_data.ps1
.EXAMPLE
    .\dummy_data.ps1 -Clear
#>
param(
    [switch]$Clear
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
if (-not $root) { $root = (Get-Location).Path }

$serverDir = Join-Path $root 'server'
$picturesDir = Join-Path $root 'assets\event_pictures_dummy'
if (-not (Test-Path (Join-Path $serverDir 'database_core.py'))) {
    throw "server\database_core.py not found. Run this script from the project root."
}

$python = $null
foreach ($candidate in @('python', 'py', 'python3')) {
    $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($cmd) { $python = $cmd.Source; break }
}
if (-not $python) { throw "Python was not found on PATH." }

$seedCode = @'
import os
import sys
from datetime import date, timedelta

server_dir, pictures_dir, mode = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, server_dir)

import database_core as core
import database_events as ev

core.init_db()  # creates the database / brings the schema up to date first
with core._connect() as _conn:
    ev._ensure_reviews_table(_conn)  # reviews is normally created on first use; a fresh database has none yet

VENDOR = "vendor@email.com"
STAFF = "staff@email.com"
PARTNER = "partner@email.com"
DISPATCHER = "dispatcher@email.com"
CUSTOMER = "customer@email.com"
ADMIN = "admin@email.com"
DEMO_PASSWORD = "demo1234"
IMAGE_DIR = os.path.join(server_dir, "event_images")
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
EVERY_DAY = ", ".join(WEEKDAYS)
TODAY = date.today()


def maps(query):
    return "https://www.google.com/maps/search/?api=1&query=" + query.replace(" ", "+")


VENUES = {
    "marina": ("Dubai Marina Yacht Club", "Dubai Marina, Dubai", maps("Dubai Marina Yacht Club")),
    "qudra": ("Al Qudra Desert Camp", "Al Qudra Road, Dubai", maps("Al Qudra Lakes Dubai")),
    "downtown": ("Downtown Rooftop Terrace", "Mohammed Bin Rashid Blvd, Dubai", maps("Downtown Dubai")),
}

CATEGORIES = ["Yacht Cruise", "Overnight Camp", "Desert Adventure", "Fine Dining"]

# key: (title, category, price AED, venue key, recurring?, days or one-time offset, time, capacity, picture, description)
EVENTS = {
    "cruise": ("Dubai Marina Sunset Yacht Cruise", "Yacht Cruise", 350, "marina", True, EVERY_DAY, "18:00", 20, "marina.png",
               "A two-hour cruise along Dubai Marina, past Ain Dubai and the Palm Jumeirah skyline as the sun sets. "
               "Soft drinks, canapes and a live DJ on the upper deck are included."),
    "camp": ("Al Qudra Overnight Desert Camp", "Overnight Camp", 650, "qudra", True, "Friday, Saturday", "16:00", 30, "desert.jpg",
             "Drive into the Al Qudra dunes for camel rides and sandboarding, then a Bedouin-style BBQ, stargazing with a guide "
             "and a night in a private tent. Breakfast at sunrise before the transfer back."),
    "dunes": ("Morning Dune Bashing Adventure", "Desert Adventure", 180, "qudra", True, EVERY_DAY, "08:00", 24, "desert.jpg",
              "Beat the heat with an early 4x4 dune bashing run, quad biking and Arabic coffee at a desert lookout. "
              "Back in the city before lunch."),
    "chef": ("Chef's Table Arabian Feast", "Fine Dining", 275, "downtown", True, "Thursday, Friday", "19:30", 16, "dinner.jpg",
             "A seven-course tasting menu of modern Emirati and Levantine dishes, served at a shared chef's table with "
             "views of the Dubai Fountain."),
    "rooftop": ("Arabian Nights Rooftop Dinner", "Fine Dining", 420, "downtown", False, 14, "20:00", 40, "dinner.jpg",
                "A one-night-only rooftop dinner with oud and qanun musicians, a mezze spread and a mixed grill, under "
                "lanterns overlooking Downtown Dubai."),
    "fireworks": ("Marina Fireworks Dinner Cruise", "Yacht Cruise", 780, "marina", False, 21, "21:00", 20, "marina.png",
                  "A three-course dinner on board a luxury yacht, timed to watch the fireworks over the Marina and Bluewaters "
                  "from the water."),
}

VEHICLES = [
    ("80937", "mini-yacht", "Dubai Marina Pier 3", "cruise"),
    ("90148", "RTA bus", "Al Qudra Road", "camp"),
    ("11259", "tesla sedan", "Dubai Downtown", None),
    ("12360", "4x4 toyota landcrusier", "Al Qudra Road", None),
]

# email, currency, signed up this many days ago (older than their first booking)
CUSTOMERS = [
    ("layla.hassan@example.com", "EUR", 400),
    ("james.carter@example.com", "GBP", 120),
    ("sofia.rossi@example.com", "USD", 45),
    ("omar.khalid@example.com", "AED", 25),
]

# Non-customer accounts must have a 16-digit SSN (only its hash and last 4 digits are stored).
# email, role, SSN, signed up N days ago
TEAM_MEMBERS = [
    ("nadia.saleh@example.com", "Staff", "5021884736190427", 200),
    ("desert.routes@example.com", "Partner", "6130597248816352", 90),
    ("karim.dispatch@example.com", "Dispatcher", "7249013658427781", 60),
]

# email, event key, when ("+N" upcoming / "-N" past / "today"), guests, ticket status, client name, rating, comment
BOOKINGS = [
    (CUSTOMER, "cruise", "+3", 2, "Valid", "", None, ""),
    (CUSTOMER, "camp", "+5", 4, "Valid", "", None, ""),
    (CUSTOMER, "rooftop", None, 2, "Valid", "", None, ""),
    (CUSTOMER, "dunes", "+8", 3, "Cancelled", "", None, ""),
    (CUSTOMER, "dunes", "-10", 2, "Used", "", 4.5, "Great driver and the dunes were amazing. Go early, it gets hot fast!"),
    (CUSTOMER, "cruise", "-20", 3, "Used", "", 5.0, "Perfect sunset, friendly crew and the canapes were delicious."),
    (CUSTOMER, "chef", "-6", 2, "Valid", "", 4.0, "Lovely food and a great view of the fountain. Service was a little slow."),
    ("layla.hassan@example.com", "cruise", "today", 2, "Valid", "", None, ""),
    ("layla.hassan@example.com", "camp", "-9", 2, "Used", "", 5.0, "The best night of our trip. Stargazing was unforgettable."),
    ("layla.hassan@example.com", "fireworks", None, 2, "Valid", "", None, ""),
    ("james.carter@example.com", "dunes", "today", 3, "Used", "", None, ""),
    ("james.carter@example.com", "chef", "-13", 4, "Used", "", 3.5, "Interesting dishes, but the portions were small for the price."),
    ("james.carter@example.com", "cruise", "-4", 2, "Used", "", 4.5, "Smooth trip and great photos of Ain Dubai."),
    ("sofia.rossi@example.com", "dunes", "today", 2, "Valid", "", None, ""),
    ("sofia.rossi@example.com", "rooftop", None, 4, "Valid", "", None, ""),
    ("sofia.rossi@example.com", "camp", "-16", 3, "Used", "", 4.0, "Tents were comfortable and the BBQ was tasty."),
    ("omar.khalid@example.com", "cruise", "today", 4, "Used", "", None, ""),
    ("omar.khalid@example.com", "dunes", "-3", 5, "Used", "", 3.0, "Fun, but we waited 30 minutes for the pickup."),
    ("omar.khalid@example.com", "chef", "+2", 2, "Valid", "", None, ""),
    (PARTNER, "camp", "+12", 8, "Valid", "Gulf Horizons Travel", None, ""),
    (PARTNER, "fireworks", None, 6, "Valid", "Al Noor Corporate Events", None, ""),
    (PARTNER, "cruise", "+6", 5, "Valid", "Sunrise Tours LLC", None, ""),
]

# event key, when, guests, client name
PARTNER_CART = [
    ("dunes", "+4", 6, "Desert Rose Holidays"),
    ("rooftop", None, 10, "Emirates Business Club"),
]

# email, event key, subject, message, resolved?
SUPPORT_TICKETS = [
    (CUSTOMER, "camp", "Change pickup location",
     "Could the transfer pick us up from our hotel in JBR instead of Downtown? Thank you.", False),
    (CUSTOMER, "rooftop", "Dietary requirements",
     "One of our guests is vegetarian and has a nut allergy. Can the menu be adjusted?", False),
    (CUSTOMER, "dunes", "Refund for cancelled booking",
     "I cancelled my dune bashing booking. When will the refund reach my card?", True),
    ("layla.hassan@example.com", "cruise", "Bringing a birthday cake",
     "It is my husband's birthday on the cruise. Are we allowed to bring our own cake on board?", False),
    ("james.carter@example.com", "chef", "Receipt for my company",
     "Please could you send a VAT receipt addressed to Carter Consulting Ltd for my chef's table booking?", True),
]


# reporter, what, about whom, their email, summary, details, resolved?
REPORTS = [
    (CUSTOMER, "Rude or unprofessional behaviour", "Driver / dispatcher", "", "Driver was rude at pickup",
     "The 4x4 driver for the morning dune bashing shouted at us for being two minutes late and drove off before we were seated.", False),
    ("omar.khalid@example.com", "Payment or refund problem", "Vendor (event organiser)", VENDOR, "Charged twice for one booking",
     "My card was charged twice for the dune bashing booking three days ago. Only one booking shows in My Bookings.", False),
    (STAFF, "Fake or reused ticket", "Customer", "james.carter@example.com", "Same ticket scanned twice",
     "A guest tried to check in a second group with a ticket that had already been used at the dune bashing today.", False),
    (PARTNER, "Experience not as described", "Vendor", VENDOR, "Camp tents were shared",
     "My clients booked private tents for the overnight camp but were placed in a shared tent with another group.", True),
]


def ensure_seed_table(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS demo_seed (tbl TEXT NOT NULL, row_id INTEGER NOT NULL)")


def seeded_ids(conn, tbl):
    return [r[0] for r in conn.execute("SELECT row_id FROM demo_seed WHERE tbl = ?", (tbl,))]


def in_list(ids):
    return "(" + ",".join(str(int(i)) for i in ids) + ")" if ids else "(NULL)"


def clear_seed():
    with core._connect() as conn:
        ensure_seed_table(conn)
        event_ids = seeded_ids(conn, "events")
        user_rowids = seeded_ids(conn, "users")
        seeded_emails = [r[0].lower() for r in conn.execute(f"SELECT email FROM users WHERE rowid IN {in_list(user_rowids)}")]
        emails_sql = "(" + ",".join("?" for _ in seeded_emails) + ")" if seeded_emails else "(NULL)"

        # Bookings the script made, plus any booking on a seeded event or by a seeded customer.
        booking_rows = conn.execute(
            f"SELECT id, ticket_code FROM bookings WHERE id IN {in_list(seeded_ids(conn, 'bookings'))} "
            f"OR event_id IN {in_list(event_ids)} OR lower(customer_email) IN {emails_sql}",
            seeded_emails,
        ).fetchall()
        booking_ids = [r[0] for r in booking_rows]
        codes = [r[1] for r in booking_rows]
        conn.execute(f"DELETE FROM reviews WHERE booking_id IN {in_list(booking_ids)} OR event_id IN {in_list(event_ids)} "
                     f"OR id IN {in_list(seeded_ids(conn, 'reviews'))}")
        if codes:
            conn.execute(f"DELETE FROM tickets WHERE ticket_code IN ({','.join('?' for _ in codes)})", codes)
        conn.execute(f"DELETE FROM tickets WHERE id IN {in_list(seeded_ids(conn, 'tickets'))}")
        conn.execute(f"DELETE FROM bookings WHERE id IN {in_list(booking_ids)}")
        conn.execute(f"DELETE FROM partner_cart WHERE id IN {in_list(seeded_ids(conn, 'partner_cart'))} "
                     f"OR event_id IN {in_list(event_ids)}")
        conn.execute(f"DELETE FROM support_tickets WHERE id IN {in_list(seeded_ids(conn, 'support_tickets'))} "
                     f"OR lower(customer_email) IN {emails_sql}", seeded_emails)

        vehicle_ids = seeded_ids(conn, "vehicles")
        conn.execute(f"DELETE FROM event_vehicles WHERE id IN {in_list(seeded_ids(conn, 'event_vehicles'))} "
                     f"OR event_id IN {in_list(event_ids)} OR vehicle_id IN {in_list(vehicle_ids)}")
        conn.execute(f"DELETE FROM vehicles WHERE id IN {in_list(vehicle_ids)}")
        conn.execute(f"DELETE FROM events WHERE id IN {in_list(event_ids)}")
        # Keep a seeded venue if someone has since put their own event there.
        conn.execute(f"DELETE FROM venues WHERE id IN {in_list(seeded_ids(conn, 'venues'))} "
                     f"AND id NOT IN (SELECT venue_id FROM events WHERE venue_id IS NOT NULL)")
        conn.execute(f"DELETE FROM vendor_categories WHERE id IN {in_list(seeded_ids(conn, 'vendor_categories'))}")
        conn.execute(f"DELETE FROM reports WHERE id IN {in_list(seeded_ids(conn, 'reports'))} "
                     f"OR lower(reporter_email) IN {emails_sql}", seeded_emails)
        conn.execute(f"DELETE FROM users WHERE rowid IN {in_list(user_rowids)}")
        conn.execute("DELETE FROM demo_seed")

    for event_id in event_ids:
        try:
            os.remove(os.path.join(IMAGE_DIR, f"{int(event_id)}.jpg"))
        except FileNotFoundError:
            pass
    print(f"Removed previously seeded data ({len(event_ids)} events, {len(booking_ids)} bookings).")


def save_picture(event_id, filename):
    path = os.path.join(pictures_dir, filename)
    if not os.path.exists(path):
        print(f"  (picture {filename} not found, event {event_id} has no picture)")
        return
    try:
        from PIL import Image, ImageOps
    except ImportError:
        print("  (Pillow is not installed, skipping event pictures: python -m pip install pillow)")
        return
    img = ImageOps.exif_transpose(Image.open(path))
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1])
        img = background
    else:
        img = img.convert("RGB")
    img.thumbnail((1400, 1400))
    os.makedirs(IMAGE_DIR, exist_ok=True)
    img.save(os.path.join(IMAGE_DIR, f"{int(event_id)}.jpg"), "JPEG", quality=85)


def occurrence(event, when):
    """The date of a booking: one-time events use their own date; recurring ones use the nearest allowed weekday."""
    _, _, _, _, recurring, days, _, _, _, _ = event
    if not recurring:
        return TODAY + timedelta(days=days)
    if when == "today":
        return TODAY
    offset = int(when)
    allowed = {d.strip() for d in days.split(",")}
    step = 1 if offset > 0 else -1
    day = TODAY + timedelta(days=offset)
    while WEEKDAYS[day.weekday()] not in allowed or day == TODAY:
        day += timedelta(days=step)
    return day


def seed():
    with core._connect() as conn:
        ensure_seed_table(conn)

        def track(tbl, row_id):
            conn.execute("INSERT INTO demo_seed (tbl, row_id) VALUES (?, ?)", (tbl, row_id))
            return row_id

        for email, role, ssn, signed_up_days_ago in TEAM_MEMBERS:
            if core.ssn_error(role, ssn):
                raise ValueError(f"Seed SSN for {email} is not valid: {core.ssn_error(role, ssn)}")
            if conn.execute("SELECT 1 FROM users WHERE lower(email) = lower(?)", (email,)).fetchone():
                continue
            signed_up = f"{(TODAY - timedelta(days=signed_up_days_ago)).isoformat()} 11:20:00"
            cur = conn.execute(
                "INSERT INTO users (email, password, role, phone, created_at, ssn_hash, ssn_last4) VALUES (?, ?, ?, NULL, ?, ?, ?)",
                (email, core.hash_password(DEMO_PASSWORD), role, signed_up, core.hash_password(ssn), ssn[-4:]),
            )
            track("users", cur.lastrowid)

        for email, currency, signed_up_days_ago in CUSTOMERS:
            if conn.execute("SELECT 1 FROM users WHERE lower(email) = lower(?)", (email,)).fetchone():
                continue  # a real account with that email already exists; leave it alone
            signed_up = f"{(TODAY - timedelta(days=signed_up_days_ago)).isoformat()} 14:05:00"
            cur = conn.execute("INSERT INTO users (email, password, role, phone, currency, created_at) VALUES (?, ?, 'Customer', NULL, ?, ?)",
                               (email, core.hash_password(DEMO_PASSWORD), currency, signed_up))
            track("users", cur.lastrowid)

        venue_ids = {}
        for key, (name, address, maps_url) in VENUES.items():
            row = conn.execute("SELECT id FROM venues WHERE name = ? AND lower(vendor_email) = lower(?)", (name, VENDOR)).fetchone()
            if row:
                venue_ids[key] = row[0]
                continue
            cur = conn.execute("INSERT INTO venues (name, address, vendor_email, maps_url) VALUES (?, ?, ?, ?)",
                               (name, address, VENDOR, maps_url))
            venue_ids[key] = track("venues", cur.lastrowid)

        for name in CATEGORIES:
            if conn.execute("SELECT 1 FROM vendor_categories WHERE lower(vendor_email) = lower(?) AND lower(name) = lower(?)",
                            (VENDOR, name)).fetchone():
                continue
            cur = conn.execute("INSERT INTO vendor_categories (vendor_email, name) VALUES (?, ?)", (VENDOR, name))
            track("vendor_categories", cur.lastrowid)

        event_ids = {}
        for key, event in EVENTS.items():
            title, category, price, venue, recurring, days, time, capacity, picture, description = event
            if recurring:
                first = occurrence(event, "+1")
                values = ("Recurring", days, f"{first.isoformat()} {time}")
            else:
                values = ("One-Time", "N/A", f"{occurrence(event, None).isoformat()} {time}")
            cur = conn.execute(
                "INSERT INTO events (title, category, price, description, vendor_email, venue_id, event_datetime, "
                "is_recurring, recur_day, recur_time, capacity) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (title, category, f"{price} AED", description, VENDOR, venue_ids[venue], values[2], values[0], values[1], time, capacity),
            )
            event_ids[key] = track("events", cur.lastrowid)

        for license_number, vehicle_type, location, event_key in VEHICLES:
            if conn.execute("SELECT 1 FROM vehicles WHERE license_number = ?", (license_number,)).fetchone():
                continue
            status = "Assigned" if event_key else "Available"
            cur = conn.execute(
                "INSERT INTO vehicles (license_number, vehicle_type, location, status, dispatcher_email, auto_reassign_recurring) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (license_number, vehicle_type, location, status, DISPATCHER, 1 if event_key else 0),
            )
            vehicle_id = track("vehicles", cur.lastrowid)
            if event_key:
                cur = conn.execute("INSERT INTO event_vehicles (event_id, vehicle_id, status) VALUES (?, ?, 'Assigned')",
                                   (event_ids[event_key], vehicle_id))
                track("event_vehicles", cur.lastrowid)

        venue_names = {key: VENUES[EVENTS[key][3]][0] for key in EVENTS}
        for email, key, when, guests, ticket_status, client_name, rating, comment in BOOKINGS:
            event = EVENTS[key]
            day = occurrence(event, when)
            code = ev._new_ticket_code(conn)
            _, _, total = ev.add_vat(event[2] * guests)
            booking_status = "Cancelled" if ticket_status == "Cancelled" else "Confirmed"
            cur = conn.execute("INSERT INTO tickets (ticket_code, event_title, customer_email, status) VALUES (?, ?, ?, ?)",
                               (code, event[0], email, ticket_status))
            track("tickets", cur.lastrowid)
            created = min(day, TODAY) - timedelta(days=7)
            cur = conn.execute(
                "INSERT INTO bookings (customer_email, event_id, event_title, venue_name, booking_date, event_time, guests, "
                "total_price, ticket_code, status, client_name, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (email, event_ids[key], event[0], venue_names[key], day.isoformat(), event[6], guests, total, code,
                 booking_status, client_name, f"{created.isoformat()} 10:15:00"),
            )
            booking_id = track("bookings", cur.lastrowid)
            if booking_status == "Cancelled":
                # Cancelled by the customer well before the 48 hour mark: full refund, VAT included.
                conn.execute(
                    "UPDATE bookings SET cancelled_at = ?, cancelled_by = ?, cancelled_by_role = 'Customer', "
                    "cancel_reason = 'Change of plans', refund_percent = 100, refund_amount = ? WHERE id = ?",
                    (f"{(TODAY - timedelta(days=1)).isoformat()} 18:40:00", email, total, booking_id),
                )
            if rating is not None:
                stamp = f"{(day + timedelta(days=1)).isoformat()} 12:00:00"
                cur = conn.execute(
                    "INSERT INTO reviews (booking_id, event_id, customer_email, rating, comment, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (booking_id, event_ids[key], email, rating, comment, stamp, stamp),
                )
                track("reviews", cur.lastrowid)

        for key, when, guests, client_name in PARTNER_CART:
            cur = conn.execute("INSERT INTO partner_cart (partner_email, event_id, booking_date, guests, client_name) VALUES (?, ?, ?, ?, ?)",
                               (PARTNER, event_ids[key], occurrence(EVENTS[key], when).isoformat(), guests, client_name))
            track("partner_cart", cur.lastrowid)

        for index, (email, key, subject, message, resolved) in enumerate(SUPPORT_TICKETS):
            created = f"{(TODAY - timedelta(days=len(SUPPORT_TICKETS) - index)).isoformat()} 09:30:00"
            cur = conn.execute(
                "INSERT INTO support_tickets (customer_email, event_title, subject, message, status, created_at, resolved_by, resolved_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (email, EVENTS[key][0], subject, message, "Resolved" if resolved else "Open", created,
                 STAFF if resolved else None, f"{TODAY.isoformat()} 08:00:00" if resolved else None),
            )
            track("support_tickets", cur.lastrowid)

        for index, (email, category, offender_type, offender_email, subject, details, resolved) in enumerate(REPORTS):
            created = f"{(TODAY - timedelta(days=len(REPORTS) - index)).isoformat()} 11:20:00"
            reporter_role = conn.execute("SELECT role FROM users WHERE lower(email) = lower(?)", (email,)).fetchone()
            cur = conn.execute(
                "INSERT INTO reports (reporter_email, reporter_role, category, offender_type, offender_email, subject, description, "
                "status, created_at, resolved_by, resolved_at, resolution) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (email, reporter_role[0] if reporter_role else "Customer", category, offender_type, offender_email, subject, details,
                 "Resolved" if resolved else "Open", created, ADMIN if resolved else None,
                 f"{TODAY.isoformat()} 08:30:00" if resolved else None, "Resolved" if resolved else ""),
            )
            track("reports", cur.lastrowid)

    for key, event_id in event_ids.items():
        save_picture(event_id, EVENTS[key][8])

    print(f"Seeded {len(event_ids)} events, {len(BOOKINGS)} bookings, {sum(1 for b in BOOKINGS if b[6] is not None)} reviews, "
          f"{len(SUPPORT_TICKETS)} support tickets, {len(REPORTS)} reports, {len(PARTNER_CART)} partner cart items.")
    print(f"Extra demo customers (password {DEMO_PASSWORD}): " + ", ".join(c[0] for c in CUSTOMERS))
    print(f"Extra team accounts (password {DEMO_PASSWORD}): " + ", ".join(f"{m[0]} ({m[1]})" for m in TEAM_MEMBERS))


clear_seed()
if mode != "clear":
    seed()
'@

$tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("rihla_dummy_data_{0}" -f [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tempDir | Out-Null
$tempFile = Join-Path $tempDir 'seed.py'
[System.IO.File]::WriteAllText($tempFile, $seedCode, [System.Text.UTF8Encoding]::new($false))
try {
    $mode = if ($Clear) { 'clear' } else { 'seed' }
    & $python $tempFile $serverDir $picturesDir $mode
    if ($LASTEXITCODE -ne 0) { throw "Seeding failed (python exited with code $LASTEXITCODE)." }
    if (-not $Clear) {
        Write-Host "Done. Restart the client (or reopen screens) to see the new data." -ForegroundColor Green
    }
}
finally {
    Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
}
