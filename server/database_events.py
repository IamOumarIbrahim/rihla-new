from datetime import date, datetime, time as dtime
from decimal import Decimal, ROUND_HALF_UP
import re
import secrets
from urllib.parse import urlparse
from database_core import _connect, _now, is_admin, get_role, get_staff_venue, DEFAULT_EVENT_CAPACITY, MAX_EVENT_CAPACITY, MAX_GUESTS_PER_BOOKING


# VAT that is added on top of every booking
VAT_RATE = 0.05

# cancel policy for customers and partners (hours before the event starts)
# 48h or more = full refund, 24h to 48h = half refund, under 24h cant cancel
# vendor or admin cancelling (or deleting the event) always gives the full refund
FULL_REFUND_HOURS = 48
HALF_REFUND_HOURS = 24
MAX_CANCEL_REASON = 300


# gives back (base, vat, total) rounded to 2 decimals
def add_vat(base_price):
    if not base_price:
        base_price = 0
    base = round(float(base_price), 2)
    vat = round(base * VAT_RATE, 2)
    total = round(base + vat, 2)
    return base, vat, total


# '240 AED' or 240 -> 240
def price_to_int(price_text):
    digits = ""
    for c in str(price_text):
        if c in "0123456789":
            digits = digits + c
    if digits:
        return int(digits)
    return 0


# '1234567890123456' -> '1234 5678 9012 3456'
def format_ticket_code(code):
    if not code:
        code = ""
    code = code.replace(" ", "").strip()
    if len(code) != 16:
        return code
    result = ""
    for i in range(0, len(code), 4):
        if result != "":
            result = result + " "
        result = result + code[i:i + 4]
    return result


# new 16 digit ticket code that is not in the tickets table yet
def _new_ticket_code(conn):
    while True:
        number = secrets.randbelow(9000000000000000) + 1000000000000000
        code = str(number)
        exists = conn.execute("SELECT 1 FROM tickets WHERE ticket_code = ?", (code,)).fetchone()
        if not exists:
            return code


# ====== Venues ======
def get_all_venues():
    with _connect() as conn:
        rows = conn.execute("SELECT id, name, address, maps_url FROM venues").fetchall()
    venues = []
    for r in rows:
        venues.append({"id": r[0], "name": r[1], "address": r[2], "maps_url": r[3] or ""})
    return venues


def get_venues_by_vendor(vendor_email):
    with _connect() as conn:
        rows = conn.execute("SELECT id, name, address, maps_url FROM venues WHERE vendor_email = ?", (vendor_email,)).fetchall()
    venues = []
    for r in rows:
        venues.append({"id": r[0], "name": r[1], "address": r[2], "maps_url": r[3] or ""})
    return venues


def create_venue(name, address, vendor_email, maps_url=""):
    with _connect() as conn:
        conn.execute("INSERT INTO venues (name, address, vendor_email, maps_url) VALUES (?, ?, ?, ?)", (name, address, vendor_email, maps_url))


# returns False and deletes nothing if events still use the venue or staff work there
def delete_venue(venue_id):
    with _connect() as conn:
        in_use = conn.execute(
            "SELECT 1 FROM events WHERE venue_id = ? UNION ALL SELECT 1 FROM users WHERE venue_id = ? LIMIT 1",
            (venue_id, venue_id),
        ).fetchone()
        if in_use:
            return False
        conn.execute("DELETE FROM venues WHERE id = ?", (venue_id,))
    return True


# Vendor categories
def get_vendor_categories(vendor_email):
    with _connect() as conn:
        rows = conn.execute("SELECT id, name FROM vendor_categories WHERE vendor_email = ?", (vendor_email,)).fetchall()
    cats = []
    for r in rows:
        cats.append({"id": r[0], "name": r[1]})
    return cats


def add_vendor_category(vendor_email, name):
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


# ====== Events ======
def _capacity_or_default(value):
    if value is None:
        return DEFAULT_EVENT_CAPACITY
    value = int(value)
    if value < 1 or value > MAX_EVENT_CAPACITY:
        raise ValueError("Capacity must be between 1 and " + str(MAX_EVENT_CAPACITY) + ".")
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
            SELECT e.id, e.title, e.category, e.price, e.description, e.vendor_email, v.name, e.event_datetime, e.is_recurring, e.recur_day, e.recur_time, e.venue_id, e.capacity, v.maps_url
            FROM events e LEFT JOIN venues v ON e.venue_id = v.id
        ''').fetchall()
    events = []
    for r in rows:
        events.append({"id": r[0], "title": r[1], "category": r[2], "price": r[3], "desc": r[4], "vendor_email": r[5], "venue_name": r[6], "event_datetime": r[7], "is_recurring": r[8], "recur_day": r[9], "recur_time": r[10], "venue_id": r[11], "capacity": r[12], "maps_url": r[13] or ""})
    return events


def get_events_by_vendor(vendor_email):
    with _connect() as conn:
        rows = conn.execute('''
            SELECT e.id, e.title, e.category, e.price, e.description, e.vendor_email, v.name, e.event_datetime, e.is_recurring, e.recur_day, e.recur_time, e.venue_id, e.capacity, v.maps_url
            FROM events e LEFT JOIN venues v ON e.venue_id = v.id WHERE e.vendor_email = ?
        ''', (vendor_email,)).fetchall()
    events = []
    for r in rows:
        events.append({"id": r[0], "title": r[1], "category": r[2], "price": r[3], "desc": r[4], "vendor_email": r[5], "venue_name": r[6], "event_datetime": r[7], "is_recurring": r[8], "recur_day": r[9], "recur_time": r[10], "venue_id": r[11], "capacity": r[12], "maps_url": r[13] or ""})
    return events


def get_events_by_venue(venue_id):
    with _connect() as conn:
        rows = conn.execute('''
            SELECT id, title, category, price, description, vendor_email, venue_id, event_datetime, is_recurring, recur_day, recur_time
            FROM events WHERE venue_id = ?
        ''', (venue_id,)).fetchall()
    events = []
    for r in rows:
        events.append({"id": r[0], "title": r[1], "category": r[2], "price": r[3], "desc": r[4], "vendor_email": r[5], "venue_id": r[6], "event_datetime": r[7], "is_recurring": r[8], "recur_day": r[9], "recur_time": r[10]})
    return events


def update_event(event_id, title, category, price, description, venue_id, event_datetime, is_recurring, recur_day, recur_time, capacity=None):
    new_capacity = None
    if capacity is not None:
        new_capacity = _capacity_or_default(capacity)
    with _connect() as conn:
        if new_capacity is not None:
            conn.execute("UPDATE events SET capacity = ? WHERE id = ?", (new_capacity, event_id))
        conn.execute(
            "UPDATE events SET title = ?, category = ?, price = ?, description = ?, venue_id = ?, event_datetime = ?, is_recurring = ?, recur_day = ?, recur_time = ? WHERE id = ?",
            (title, category, price, description, venue_id, event_datetime, is_recurring, recur_day, recur_time, event_id)
        )
        # bookings and tickets keep the title so change it there too
        conn.execute("UPDATE bookings SET event_title = ? WHERE event_id = ?", (title, event_id))
        conn.execute(
            "UPDATE tickets SET event_title = ? WHERE ticket_code IN (SELECT ticket_code FROM bookings WHERE event_id = ?)",
            (title, event_id),
        )


def delete_event(event_id):
    with _connect() as conn:
        owner = conn.execute("SELECT vendor_email FROM events WHERE id = ?", (event_id,)).fetchone()
        vendor_email = ""
        if owner:
            vendor_email = owner[0]
        conn.execute(
            "UPDATE vehicles SET status = 'Available' WHERE status = 'Assigned' AND id IN "
            "(SELECT vehicle_id FROM event_vehicles WHERE event_id = ? AND status = 'Assigned')",
            (event_id,),
        )
        conn.execute("DELETE FROM event_vehicles WHERE event_id = ?", (event_id,))
        # upcoming bookings that are not used get cancelled with full refund, old ones stay the same
        conn.execute(
            "UPDATE bookings SET status = 'Cancelled', cancelled_at = ?, cancelled_by = ?, cancelled_by_role = 'Vendor', "
            "cancel_reason = ?, refund_percent = 100, refund_amount = total_price "
            "WHERE event_id = ? AND status = 'Confirmed' AND booking_date >= ? "
            "AND ticket_code IN (SELECT ticket_code FROM tickets WHERE status = 'Valid')",
            (_now(), vendor_email, "The vendor removed this event.", event_id, date.today().isoformat()),
        )
        conn.execute(
            "UPDATE tickets SET status = 'Cancelled' WHERE status = 'Valid' "
            "AND ticket_code IN (SELECT ticket_code FROM bookings WHERE event_id = ? AND status = 'Cancelled')",
            (event_id,),
        )
        conn.execute("DELETE FROM events WHERE id = ?", (event_id,))


# confirmed bookings from today on
def count_active_bookings(event_id):
    with _connect() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM bookings WHERE event_id = ? AND status = 'Confirmed' AND booking_date >= ?",
            (event_id, date.today().isoformat()),
        ).fetchone()[0]
    return count


# (number of bookings, guests booked) counting today and later only
def get_event_demand(event_id):
    with _connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(guests), 0) FROM bookings "
            "WHERE event_id = ? AND status = 'Confirmed' AND booking_date >= ?",
            (event_id, date.today().isoformat()),
        ).fetchone()
    if row:
        return (row[0], row[1])
    return (0, 0)


# todays events with bookings and check ins, with venue_id only that venue
def get_events_today(venue_id=None):
    today = date.today().isoformat()
    weekday = date.today().strftime("%A")
    with _connect() as conn:
        rows = conn.execute('''
            SELECT e.id, e.title, e.event_datetime, e.recur_time, e.is_recurring, e.recur_day, v.name, v.maps_url
            FROM events e LEFT JOIN venues v ON v.id = e.venue_id
            WHERE ? IS NULL OR e.venue_id = ?
            ORDER BY e.title
        ''', (venue_id, venue_id)).fetchall()

        result = []
        for r in rows:
            eid = r[0]
            title = r[1]
            dt = r[2] or ""
            recur_time = r[3]
            is_rec = r[4]
            recur_day = r[5] or ""
            venue_name = r[6]
            maps_url = r[7]

            occurs_today = False
            if is_rec == "Recurring":
                for d in recur_day.split(","):
                    if d.strip() == weekday:
                        occurs_today = True
            else:
                if dt[:10] == today:
                    occurs_today = True

            if occurs_today:
                demand = conn.execute(
                    "SELECT COUNT(*), COALESCE(SUM(guests), 0) FROM bookings "
                    "WHERE event_id = ? AND booking_date = ? AND status = 'Confirmed'",
                    (eid, today),
                ).fetchone()
                bookings_count = demand[0]
                guests_count = demand[1]

                checked_in = conn.execute(
                    "SELECT COALESCE(SUM(b.guests), 0) FROM bookings b "
                    "JOIN tickets t ON t.ticket_code = b.ticket_code "
                    "WHERE b.event_id = ? AND b.booking_date = ? AND t.status = 'Used'",
                    (eid, today),
                ).fetchone()[0]

                start_time = recur_time
                if not start_time:
                    start_time = dt[11:16]
                result.append({
                    "id": eid, "title": title, "venue_name": venue_name, "maps_url": maps_url or "",
                    "time": start_time,
                    "bookings": bookings_count, "guests": guests_count, "checked_in": checked_in,
                })
    return result


# ====== Vehicles ======
def get_vehicle_types():
    with _connect() as conn:
        rows = conn.execute("SELECT id, name, capacity FROM vehicle_types").fetchall()
    types = []
    for r in rows:
        types.append({"id": r[0], "name": r[1], "capacity": r[2]})
    return types


def get_vehicle_capacity(vehicle_type):
    with _connect() as conn:
        row = conn.execute("SELECT capacity FROM vehicle_types WHERE name = ?", (vehicle_type,)).fetchone()
    if row:
        return row[0]
    return 4


def get_all_vehicles(dispatcher_email):
    with _connect() as conn:
        rows = conn.execute('''
            SELECT v.id, v.license_number, v.vehicle_type, v.location, v.status, v.auto_reassign_recurring, vt.capacity
            FROM vehicles v LEFT JOIN vehicle_types vt ON v.vehicle_type = vt.name
            WHERE v.dispatcher_email = ?
        ''', (dispatcher_email,)).fetchall()
    vehicles = []
    for r in rows:
        seats = r[6]
        if seats is None:
            seats = 4
        vehicles.append({"id": r[0], "license_number": r[1], "vehicle_type": r[2], "location": r[3], "status": r[4], "auto_reassign_recurring": r[5], "capacity": seats})
    return vehicles


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
            conn.execute(
                "UPDATE event_vehicles SET status = 'Concluded' WHERE vehicle_id = ? AND status = 'Assigned'",
                (vehicle_id,),
            )
        conn.execute("UPDATE vehicles SET status = ? WHERE id = ?", (status, vehicle_id))


def dispatch_vehicle_combination(event_id, vehicle_assignments):
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
                conn.execute(
                    "INSERT INTO event_vehicles (event_id, vehicle_id, status) VALUES (?, ?, 'Assigned')",
                    (event_id, vid),
                )
                assigned += 1
    return assigned


# vehicle is Available again, this also ends the event it was on
def free_vehicle(vehicle_id):
    update_vehicle_status(vehicle_id, "Available")


def get_dispatches_by_event(event_id):
    with _connect() as conn:
        rows = conn.execute('''
            SELECT ev.id, v.license_number, v.vehicle_type, v.location, ev.status, v.id
            FROM event_vehicles ev JOIN vehicles v ON ev.vehicle_id = v.id
            WHERE ev.event_id = ? AND ev.status = 'Assigned'
        ''', (event_id,)).fetchall()
    dispatches = []
    for r in rows:
        dispatches.append({"dispatch_id": r[0], "license_number": r[1], "vehicle_type": r[2], "location": r[3], "status": r[4], "vehicle_id": r[5]})
    return dispatches


# ====== Capacity and Booking ======
def _event_allows_date(is_recurring, recur_day, event_datetime, day):
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    if is_recurring == "Recurring":
        if not recur_day:
            recur_day = ""
        allowed = []
        for d in recur_day.split(","):
            if d.strip() in weekday_names:
                allowed.append(d.strip())
        return weekday_names[day.weekday()] in allowed
    if not event_datetime:
        event_datetime = ""
    try:
        single = date.fromisoformat(event_datetime[:10])
    except ValueError:
        return False
    return day == single


def _capacity_info(conn, event_id, day=None):
    vehicles = conn.execute(
        "SELECT v.vehicle_type, COUNT(*), vt.capacity FROM event_vehicles ev "
        "JOIN vehicles v ON v.id = ev.vehicle_id "
        "LEFT JOIN vehicle_types vt ON vt.name = v.vehicle_type "
        "WHERE ev.event_id = ? AND ev.status = 'Assigned' "
        "GROUP BY v.vehicle_type",
        (event_id,),
    ).fetchall()

    if vehicles:
        # capacity = number of vehicles * seats of each type
        total = 0
        vehcile_details = []
        for r in vehicles:
            seats = r[2]
            if not seats:
                seats = 4
            total = total + r[1] * seats
            vehcile_details.append({"vehicle_type": r[0], "count": r[1], "seats_each": seats})
        source = "vehicles"
    else:
        row = conn.execute("SELECT capacity FROM events WHERE id = ?", (event_id,)).fetchone()
        if row and row[0]:
            total = row[0]
        else:
            total = DEFAULT_EVENT_CAPACITY
        source = "event"
        vehcile_details = []

    info = {"total": total, "source": source, "vehicles": vehcile_details, "booked": None, "remaining": None}
    if day is not None:
        booked = conn.execute(
            "SELECT COALESCE(SUM(guests), 0) FROM bookings WHERE event_id = ? AND booking_date = ? AND status = 'Confirmed'",
            (event_id, day.isoformat()),
        ).fetchone()[0]
        info["booked"] = booked
        remaining = total - booked
        if remaining < 0:
            remaining = 0
        info["remaining"] = remaining
    return info


def get_event_capacity(event_id, booking_date=None):
    day = None
    if booking_date is not None:
        if isinstance(booking_date, date):
            day = booking_date
        else:
            day = date.fromisoformat(str(booking_date))
    with _connect() as conn:
        info = _capacity_info(conn, event_id, day)
    return info


# saves a booking and makes the 16 digit ticket code
# customers can book many events and the same event again if they want
# partners can book more guests, up to all the seats left
def create_booking(customer_email, event_id, booking_date, guests, is_partner=False, client_name=""):
    with _connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        result = _book(conn, customer_email, event_id, booking_date, guests, is_partner, client_name)
    return result


# the work of create_booking, the caller already started the transaction
def _book(conn, customer_email, event_id, booking_date, guests, is_partner=False, client_name=""):
    customer_email = (customer_email or "").strip()
    client_name = (client_name or "").strip()
    try:
        day = date.fromisoformat(str(booking_date))
        guests = int(guests)
    except (TypeError, ValueError):
        return {"success": False, "message": "Invalid date or number of guests.", "booking": None}
    if not customer_email:
        return {"success": False, "message": "You must be logged in to book.", "booking": None}
    if guests < 1:
        return {"success": False, "message": "You must book at least 1 guest.", "booking": None}
    if not is_partner and guests > MAX_GUESTS_PER_BOOKING:
        return {"success": False, "message": "You can book 1 to " + str(MAX_GUESTS_PER_BOOKING) + " guests at a time.", "booking": None}
    if day < date.today():
        return {"success": False, "message": "This date is in the past. Please choose another date.", "booking": None}

    event = conn.execute(
        "SELECT e.title, e.price, e.is_recurring, e.recur_day, e.event_datetime, e.recur_time, v.name "
        "FROM events e LEFT JOIN venues v ON v.id = e.venue_id WHERE e.id = ?",
        (event_id,),
    ).fetchone()
    if not event:
        return {"success": False, "message": "This event no longer exists.", "booking": None}
    title, price, is_recurring, recur_day, event_datetime, recur_time, venue_name = event

    if not _event_allows_date(is_recurring, recur_day, event_datetime, day):
        return {"success": False, "message": "This event is not available on the date you chose.", "booking": None}

    # same customer booking the same event again is allowed
    capacity = _capacity_info(conn, event_id, day)
    if guests > capacity["remaining"]:
        if capacity["remaining"] == 0:
            msg = "Sorry, this event is fully booked on that date (capacity " + str(capacity["total"]) + ")."
            return {"success": False, "message": msg, "booking": None}
        msg = ("Not enough seats. Only " + str(capacity["remaining"]) + " of " + str(capacity["total"])
               + " seats are left on that date, and you asked for " + str(guests) + ".")
        return {"success": False, "message": msg, "booking": None}

    code = _new_ticket_code(conn)
    base, vat, total = add_vat(price_to_int(price) * guests)
    event_time = recur_time
    if not event_time:
        event_time = str(event_datetime or "")[11:16]

    conn.execute(
        "INSERT INTO tickets (ticket_code, event_title, customer_email, status) VALUES (?, ?, ?, 'Valid')",
        (code, title, customer_email),
    )
    cursor = conn.execute(
        "INSERT INTO bookings (customer_email, event_id, event_title, venue_name, booking_date, event_time, "
        "guests, total_price, ticket_code, status, client_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Confirmed', ?)",
        (customer_email, event_id, title, venue_name, day.isoformat(), event_time, guests, total, code, client_name),
    )
    booking_id = cursor.lastrowid

    return {
        "success": True,
        "message": "Booking confirmed.",
        "booking": {
            "id": booking_id, "event_title": title, "venue_name": venue_name, "booking_date": day.isoformat(),
            "event_time": event_time, "guests": guests, "total_price": total, "ticket_code": code,
            "client_name": client_name, "base_price": base, "vat": vat,
        },
    }


# ====== Bookings list and cancel ======
_BOOKING_SELECT = (
    "SELECT b.id, b.event_id, b.event_title, b.venue_name, b.booking_date, b.event_time, b.guests, "
    "b.total_price, b.ticket_code, b.status, t.status, b.client_name, b.customer_email, "
    "b.cancelled_at, b.cancelled_by, b.cancelled_by_role, b.cancel_reason, b.refund_percent, b.refund_amount "
    "FROM bookings b LEFT JOIN tickets t ON t.ticket_code = b.ticket_code "
)


# when the booked event starts, no time means midnight
def _event_start(booking_date, event_time):
    if not event_time:
        event_time = "00:00"
    hour = 0
    minute = 0
    parts = event_time.split(":")
    if len(parts) >= 2:
        try:
            h = int(parts[0])
            m = int(parts[1])
            hour = h
            minute = m
        except ValueError:
            pass
    return datetime.combine(date.fromisoformat(booking_date), dtime(hour, minute))


# refund for a customer or partner cancelling now: 100, 50 or None when its too late
def refund_percent_for(start, now=None):
    if now is None:
        now = datetime.now()
    hours_left = (start - now).total_seconds() / 3600
    if hours_left >= FULL_REFUND_HOURS:
        return 100
    if hours_left >= HALF_REFUND_HOURS:
        return 50
    return None


# (base, vat, total) of a refund, vat is refunded the same percent as the price
def split_refund(total_price, percent):
    if not total_price:
        total_price = 0
    total = round(float(total_price) * percent / 100, 2)
    base = round(total / (1 + VAT_RATE), 2)
    vat = round(total - base, 2)
    return base, vat, total


def _booking_dict(r, now):
    booking_status = r[9]
    ticket_status = r[10]
    if booking_status == "Cancelled" or ticket_status == "Cancelled":
        shown = "Cancelled"
    elif ticket_status == "Used":
        shown = "Checked in"
    elif r[4] < now.date().isoformat():
        shown = "Expired"
    else:
        shown = "Confirmed"

    refund_if_cancelled = None
    if shown == "Confirmed":
        refund_if_cancelled = refund_percent_for(_event_start(r[4], r[5]), now)
    return {
        "id": r[0], "event_id": r[1], "event_title": r[2], "venue_name": r[3], "booking_date": r[4],
        "event_time": r[5], "guests": r[6], "total_price": r[7], "ticket_code": r[8],
        "status": shown, "client_name": r[11] or "", "customer_email": r[12],
        # the booker can cancel as long as the policy still gives some refund
        "can_cancel": refund_if_cancelled is not None, "refund_if_cancelled": refund_if_cancelled,
        "cancelled_at": r[13], "cancelled_by": r[14], "cancelled_by_role": r[15], "cancel_reason": r[16] or "",
        "refund_percent": r[17], "refund_amount": r[18],
    }


def get_bookings_by_customer(customer_email):
    with _connect() as conn:
        rows = conn.execute(
            _BOOKING_SELECT + "WHERE lower(b.customer_email) = lower(?) ORDER BY b.booking_date, b.id",
            ((customer_email or "").strip(),),
        ).fetchall()
    now = datetime.now()
    bookings = []
    for r in rows:
        bookings.append(_booking_dict(r, now))
    return bookings


def get_bookings_by_vendor(vendor_email):
    with _connect() as conn:
        rows = conn.execute(
            _BOOKING_SELECT + "JOIN events e ON e.id = b.event_id "
            "WHERE lower(e.vendor_email) = lower(?) ORDER BY b.booking_date DESC, b.id DESC",
            ((vendor_email or "").strip(),),
        ).fetchall()
    now = datetime.now()
    bookings = []
    for r in rows:
        bookings.append(_booking_dict(r, now))
    return bookings


# every booking newest date first, None if not an admin
def get_all_bookings(admin_email):
    if not is_admin(admin_email):
        return None
    with _connect() as conn:
        rows = conn.execute(_BOOKING_SELECT + "ORDER BY b.booking_date DESC, b.id DESC").fetchall()
    now = datetime.now()
    bookings = []
    for r in rows:
        bookings.append(_booking_dict(r, now))
    return bookings


# cancels one booking and saves who did it, why and the refund
# owner_check(row) gives back an error message if this person cant cancel the booking
# by_operator is a vendor or admin, they can cancel until it starts and always full refund
def _cancel(booking_id, actor_email, actor_role, reason, owner_check, by_operator):
    reason = (reason or "").strip()
    if len(reason) > MAX_CANCEL_REASON:
        return {"success": False, "message": "The reason is too long (maximum " + str(MAX_CANCEL_REASON) + " characters)."}
    if by_operator and not reason:
        return {"success": False, "message": "Please give the customer a reason for the cancellation."}

    with _connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT b.ticket_code, b.booking_date, b.event_time, b.status, b.total_price, b.customer_email, e.vendor_email "
            "FROM bookings b LEFT JOIN events e ON e.id = b.event_id WHERE b.id = ?",
            (booking_id,),
        ).fetchone()
        if not row:
            problem = "Booking not found."
        else:
            problem = owner_check(row)
        if problem:
            return {"success": False, "message": problem}
        code = row[0]
        day = row[1]
        event_time = row[2]
        status = row[3]
        total_price = row[4]
        if status == "Cancelled":
            return {"success": False, "message": "This booking is already cancelled."}
        if status != "Confirmed":
            return {"success": False, "message": "This booking cannot be cancelled."}

        start = _event_start(day, event_time)
        started = datetime.now() >= start
        if by_operator:
            percent = 100
        else:
            percent = refund_percent_for(start)
        if started:
            return {"success": False, "message": "This event has already started, so the booking cannot be cancelled."}
        if percent is None:
            return {"success": False, "message": "Cancellations close " + str(HALF_REFUND_HOURS) + " hours before the event starts."}

        updated = conn.execute(
            "UPDATE tickets SET status = 'Cancelled' WHERE ticket_code = ? AND status = 'Valid'", (code,)
        ).rowcount
        if not updated:
            return {"success": False, "message": "This ticket was already used, so the booking cannot be cancelled."}
        base, vat, refund = split_refund(total_price, percent)
        conn.execute(
            "UPDATE bookings SET status = 'Cancelled', cancelled_at = ?, cancelled_by = ?, cancelled_by_role = ?, "
            "cancel_reason = ?, refund_percent = ?, refund_amount = ? WHERE id = ?",
            (_now(), (actor_email or "").strip(), actor_role, reason, percent, refund, booking_id),
        )
    msg = ("Booking cancelled. " + format(refund, ",.2f") + " AED (" + str(percent)
           + "%, VAT included) will be refunded to the original payment method.")
    return {
        "success": True,
        "message": msg,
        "refund": {"percent": percent, "base": base, "vat": vat, "total": refund},
    }


# the customer or partner that made the booking cancels it (refund policy applies)
def cancel_booking(booking_id, customer_email, reason=""):
    email = (customer_email or "").strip()

    def is_booker(row):
        if row[5].lower() == email.lower():
            return None
        return "Booking not found."
    return _cancel(booking_id, email, get_role(email), reason, is_booker, by_operator=False)


# vendor cancels a booking on one of their events (full refund, needs a reason)
def vendor_cancel_booking(booking_id, vendor_email, reason):
    email = (vendor_email or "").strip()

    def owns_event(row):
        owner = row[6] or ""
        if owner.lower() == email.lower():
            return None
        return "This booking is not for one of your events."
    return _cancel(booking_id, email, "Vendor", reason, owns_event, by_operator=True)


# admin can cancel any booking (full refund, needs a reason)
def admin_cancel_booking(booking_id, admin_email, reason):
    if not is_admin(admin_email):
        return {"success": False, "message": "Only an admin can do this."}

    def anyone(row):
        return None
    return _cancel(booking_id, admin_email, "Admin", reason, anyone, by_operator=True)


# venue of the event a ticket is for, from the booking or from the event title if there is no booking
def _ticket_venue_id(conn, ticket_code, event_title):
    row = conn.execute(
        "SELECT e.venue_id FROM bookings b JOIN events e ON e.id = b.event_id WHERE b.ticket_code = ?", (ticket_code,)
    ).fetchone()
    if row is None:
        row = conn.execute("SELECT venue_id FROM events WHERE title = ? ORDER BY id LIMIT 1", (event_title,)).fetchone()
    if row:
        return row[0]
    return None


# checks a ticket in  with venue_id a ticket for another venue is refused and we dont say
# anything about it (staff only see their own venue)
def verify_ticket_code(ticket_code, expected_event_title=None, venue_id=None):
    with _connect() as conn:
        row = conn.execute(
            "SELECT event_title, customer_email, status FROM tickets WHERE ticket_code = ?", (ticket_code,)
        ).fetchone()
        ticket_venue = None
        if row:
            ticket_venue = _ticket_venue_id(conn, ticket_code, row[0])
    if not row:
        return {"success": False, "message": "Invalid ticket code. Not found in system."}
    if venue_id is not None and ticket_venue != venue_id:
        return {"success": False, "message": "This ticket is not for an event at your venue. Entry refused."}

    event_title = row[0]
    customer_email = row[1]
    status = row[2]
    if expected_event_title and event_title != expected_event_title:
        return {"success": False, "message": "Wrong event. This ticket is for " + str(event_title) + "."}
    if status == "Cancelled":
        return {"success": False, "message": "This ticket was cancelled. Entry refused."}
    if status == "Used":
        return {"success": False, "message": "Ticket already used! Checked in previously."}

    with _connect() as conn:
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
        note = " Admit " + str(booking[0]) + " guest(s)."
        if booking[1] != date.today().isoformat():
            note += " Note: this booking is for " + str(booking[1]) + ", not today."
    return {"success": True, "message": "Access granted! Ticket valid for " + str(event_title) + " (" + str(customer_email) + ")." + note}


# check in from the scanner, only staff and only for events at their venue
def staff_verify_ticket(staff_email, ticket_code, expected_event_title=None):
    venue = get_staff_venue(staff_email)
    if venue is None:
        return {"success": False, "message": "Only staff assigned to a venue can check tickets in."}
    return verify_ticket_code(ticket_code, expected_event_title, venue_id=venue["id"])


# todays schedule for the venue of the staff member, None if not staff at a venue
def get_staff_schedule(staff_email):
    venue = get_staff_venue(staff_email)
    if venue is None:
        return None
    return get_events_today(venue["id"])


# ====== Partner shopping list (cart) ======
def add_to_cart(partner_email, event_id, booking_date, guests, client_name=""):
    partner_email = (partner_email or "").strip()
    client_name = (client_name or "").strip()
    try:
        day = date.fromisoformat(str(booking_date))
        guests = int(guests)
    except (TypeError, ValueError):
        return {"success": False, "message": "Invalid date or number of guests."}

    if guests < 1:
        return {"success": False, "message": "You must book at least 1 guest."}
    if day < date.today():
        return {"success": False, "message": "This date is in the past."}

    with _connect() as conn:
        event = conn.execute(
            "SELECT title, is_recurring, recur_day, event_datetime FROM events WHERE id = ?",
            (event_id,)
        ).fetchone()
        if not event:
            return {"success": False, "message": "This event no longer exists."}
        title, is_recurring, recur_day, event_datetime = event

        if not _event_allows_date(is_recurring, recur_day, event_datetime, day):
            return {"success": False, "message": "This event is not available on that date."}

        capacity = _capacity_info(conn, event_id, day)
        if guests > capacity["remaining"]:
            if capacity["remaining"] == 0:
                return {"success": False, "message": "Sorry, this event is fully booked on that date (capacity " + str(capacity["total"]) + ")."}
            return {"success": False, "message": "Not enough seats. Only " + str(capacity["remaining"]) + " seats left on that date."}

        conn.execute(
            "INSERT INTO partner_cart (partner_email, event_id, booking_date, guests, client_name) VALUES (?, ?, ?, ?, ?)",
            (partner_email, event_id, day.isoformat(), guests, client_name)
        )
    return {"success": True, "message": "Added '" + str(title) + "' to your shopping list."}


def get_cart_items(partner_email):
    with _connect() as conn:
        rows = conn.execute(
            "SELECT c.id, c.event_id, c.booking_date, c.guests, c.client_name, e.title, e.price, v.name "
            "FROM partner_cart c "
            "JOIN events e ON e.id = c.event_id "
            "LEFT JOIN venues v ON v.id = e.venue_id "
            "WHERE lower(c.partner_email) = lower(?) ORDER BY c.id",
            ((partner_email or "").strip(),)
        ).fetchall()

    items = []
    for r in rows:
        unit_price = price_to_int(r[6])
        total_price = unit_price * r[3]
        items.append({
            "id": r[0],
            "event_id": r[1],
            "booking_date": r[2],
            "guests": r[3],
            "client_name": r[4] or "",
            "title": r[5],
            "price": r[6],
            "unit_price": unit_price,
            "venue_name": r[7] or "Unknown Venue",
            "total_price": total_price,
        })
    return items


def get_cart_count(partner_email):
    with _connect() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM partner_cart WHERE lower(partner_email) = lower(?)",
            ((partner_email or "").strip(),)
        ).fetchone()[0]
    return count


def remove_from_cart(cart_id, partner_email):
    with _connect() as conn:
        deleted = conn.execute(
            "DELETE FROM partner_cart WHERE id = ? AND lower(partner_email) = lower(?)",
            (cart_id, (partner_email or "").strip())
        ).rowcount
    return bool(deleted)


def clear_cart(partner_email):
    with _connect() as conn:
        conn.execute(
            "DELETE FROM partner_cart WHERE lower(partner_email) = lower(?)",
            ((partner_email or "").strip(),)
        )


def checkout_cart(partner_email):
    items = get_cart_items(partner_email)
    if not items:
        return {"success": False, "message": "Shopping list is empty.", "bookings": []}

    # everything is booked in one transaction, if one item fails we roll back so none of them
    # is kept (no half booked cart and no cancelled bookings left over)
    booked_results = []
    error = None
    with _connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        for item in items:
            res = _book(conn, partner_email, item["event_id"], item["booking_date"], item["guests"],
                        is_partner=True, client_name=item["client_name"])
            if not res["success"]:
                error = ("Could not book '" + str(item["title"]) + "': " + res["message"]
                         + " No booking was made and your payment was not taken.")
                conn.rollback()
                break
            booked_results.append(res["booking"])
    if error is not None:
        return {"success": False, "message": error, "bookings": []}

    clear_cart(partner_email)
    return {"success": True, "message": "Successfully confirmed " + str(len(booked_results)) + " event booking(s)!", "bookings": booked_results}


# ====== Reviews (My Experiences) ======
# customer can review a past experience, one that was checked in or the date already passed
REVIEWABLE_STATUSES = ("Checked in", "Expired")
MAX_REVIEW_COMMENT = 500


# makes the reviews table the first time we need it (so old databases still work)
def _ensure_reviews_table(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL UNIQUE,
            event_id INTEGER,
            customer_email TEXT NOT NULL,
            rating REAL NOT NULL,
            comment TEXT NOT NULL DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(booking_id) REFERENCES bookings(id)
        )
    ''')
    conn.execute("CREATE INDEX IF NOT EXISTS idx_reviews_event ON reviews(event_id)")


# past bookings of a customer newest first, each has review_rating and review_comment
def get_my_experiences(customer_email):
    experiences = []
    for b in get_bookings_by_customer(customer_email):
        if b["status"] in REVIEWABLE_STATUSES:
            experiences.append(b)
    experiences.reverse()

    with _connect() as conn:
        _ensure_reviews_table(conn)
        rows = conn.execute(
            "SELECT booking_id, rating, comment FROM reviews WHERE lower(customer_email) = lower(?)",
            ((customer_email or "").strip(),),
        ).fetchall()

    reviews = {}
    for r in rows:
        reviews[r[0]] = (r[1], r[2])
    for booking in experiences:
        if booking["id"] in reviews:
            rating = reviews[booking["id"]][0]
            comment = reviews[booking["id"]][1]
        else:
            rating = None
            comment = ""
        booking["review_rating"] = rating
        booking["review_comment"] = comment
    return experiences


# saves a review (0 to 5 in steps of 0.5), the same booking again just updates it
def submit_review(customer_email, booking_id, rating, comment=""):
    try:
        booking_id = int(booking_id)
        rating = float(rating)
    except (TypeError, ValueError):
        return {"success": False, "message": "Please choose a rating from 0 to 5."}
    if rating < 0 or rating > 5 or (rating * 2) != int(rating * 2):
        return {"success": False, "message": "The rating must be from 0 to 5, in steps of 0.5."}

    comment = (comment or "").strip()
    if len(comment) > MAX_REVIEW_COMMENT:
        return {"success": False, "message": "Your comment is too long (maximum " + str(MAX_REVIEW_COMMENT) + " characters)."}

    customer_email = (customer_email or "").strip()
    booking = None
    for b in get_bookings_by_customer(customer_email):
        if b["status"] in REVIEWABLE_STATUSES and b["id"] == booking_id:
            booking = b
    if not booking:
        return {"success": False, "message": "You can only review experiences that you already attended."}

    with _connect() as conn:
        _ensure_reviews_table(conn)
        conn.execute(
            "INSERT INTO reviews (booking_id, event_id, customer_email, rating, comment) VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(booking_id) DO UPDATE SET rating = excluded.rating, comment = excluded.comment, "
            "updated_at = CURRENT_TIMESTAMP",
            (booking_id, booking["event_id"], customer_email, rating, comment),
        )
    return {"success": True, "message": "Thank you for your review!"}


# average rating and number of reviews for every event that has reviews
# {event_id: {"average": 4.3, "count": 2}}
# average is rounded to 1 decimal and .x5 goes up (4.25 -> 4.3)
def get_event_ratings():
    with _connect() as conn:
        _ensure_reviews_table(conn)
        rows = conn.execute(
            "SELECT event_id, AVG(rating), COUNT(*) FROM reviews WHERE event_id IS NOT NULL GROUP BY event_id"
        ).fetchall()

    ratings = {}
    for event_id, average, count in rows:
        rounded = Decimal(str(round(average, 4))).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        ratings[event_id] = {"average": float(rounded), "count": count}
    return ratings


# ====== Venue map links ======
MAX_MAPS_URL_LENGTH = 500


# checks the google maps link of a venue (its optional), gives back (clean_url, error_message)
# empty is fine, only https google maps links are ok
def validate_maps_url(url):
    url = (url or "").strip()
    if not url:
        return "", None
    if len(url) > MAX_MAPS_URL_LENGTH:
        return "", "The map link is too long (maximum " + str(MAX_MAPS_URL_LENGTH) + " characters)."
    if re.search(r"\s", url):
        return "", "The map link must not contain spaces."

    if url.lower().startswith("http://"):
        url = "https://" + url[7:]
    elif "://" not in url:
        url = "https://" + url

    message = "Please use a Google Maps link, for example https://maps.app.goo.gl/... or https://www.google.com/maps/..."
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
    except ValueError:
        return "", message
    path = parsed.path or ""

    google_host = re.fullmatch(r"(?:[a-z0-9-]+\.)*google\.(?:com|co\.[a-z]{2}|com\.[a-z]{2}|[a-z]{2})", host)
    is_maps = False
    if parsed.scheme == "https" and "@" not in parsed.netloc:
        if host == "maps.app.goo.gl":
            is_maps = True
        elif host == "goo.gl" and path.startswith("/maps"):
            is_maps = True
        elif google_host and path.startswith("/maps"):
            is_maps = True
        elif google_host and host.startswith("maps.") and path in ("", "/"):
            is_maps = True
    if not is_maps:
        return "", message
    return url, None


# vendor adds, changes or removes the map link of one of their venues
def update_venue_maps_url(venue_id, vendor_email, maps_url):
    cleaned, problem = validate_maps_url(maps_url)
    if problem:
        return {"success": False, "message": problem}

    with _connect() as conn:
        cursor = conn.execute(
            "UPDATE venues SET maps_url = ? WHERE id = ? AND lower(vendor_email) = lower(?)",
            (cleaned, venue_id, (vendor_email or "").strip()),
        )
        if cursor.rowcount == 0:
            return {"success": False, "message": "Venue not found, or it belongs to another vendor."}
    if cleaned:
        msg = "Map link saved."
    else:
        msg = "Map link removed."
    return {"success": True, "message": msg, "maps_url": cleaned}
