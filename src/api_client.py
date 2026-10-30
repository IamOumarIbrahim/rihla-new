"""
api_client.py – Thin HTTP wrapper that matches the exact function signatures
of the old database.py but calls the Rihla API server instead of SQLite directly.

The server must be running at http://localhost:5000 before the Tkinter UI starts.
"""

import warnings
import requests

# Suppress urllib3 version warning
warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning if hasattr(requests.packages, 'urllib3') else Warning)

BASE_URL = "http://127.0.0.1:5000/api"
_SESSION = requests.Session()

# Re-export constants so existing imports like `from database import MAX_GUESTS_PER_BOOKING` work.
DEFAULT_EVENT_CAPACITY = 20
MAX_EVENT_CAPACITY = 5000
MAX_GUESTS_PER_BOOKING = 10
MAX_OPEN_SUPPORT_TICKETS = 3


def _get(path, **params):
    try:
        resp = _SESSION.get(f"{BASE_URL}{path}", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Cannot connect to the Rihla server. Is it running? (python server/server.py)")


def _post(path, data=None):
    try:
        resp = _SESSION.post(f"{BASE_URL}{path}", json=data or {}, timeout=10)
        return resp.json()
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Cannot connect to the Rihla server. Is it running? (python server/server.py)")


def _put(path, data=None):
    try:
        resp = _SESSION.put(f"{BASE_URL}{path}", json=data or {}, timeout=10)
        return resp.json()
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Cannot connect to the Rihla server. Is it running? (python server/server.py)")


def _delete(path):
    try:
        resp = _SESSION.delete(f"{BASE_URL}{path}", timeout=10)
        return resp.json()
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Cannot connect to the Rihla server. Is it running? (python server/server.py)")


# -----------------------------------------------------------------------
# Auth
# -----------------------------------------------------------------------

def check_login(email, password):
    return login(email, password)[0]


def login(email, password):
    """(True, "") on success, otherwise (False, the reason to show, e.g. a banned account)."""
    r = _post("/auth/login", {"email": email, "password": password})
    return r.get("success", False), r.get("message", "Invalid email or password.")


def get_role(email):
    r = _get(f"/auth/role/{email}")
    return r.get("role", "Customer")


# -----------------------------------------------------------------------
# Users
# -----------------------------------------------------------------------

def register_user(email, password, role="Customer", phone=None, ssn=None):
    r = _post("/users/register", {"email": email, "password": password, "role": role, "phone": phone, "ssn": ssn})
    return r.get("success", False)


def update_password(email, new_password):
    _put("/users/password", {"email": email, "new_password": new_password})


def get_preferred_currency(email):
    try:
        return _get(f"/users/currency/{email}").get("currency", "AED")
    except Exception:
        return "AED"


def set_preferred_currency(email, currency):
    return _put("/users/currency", {"email": email, "currency": currency}).get("success", False)


def email_exists(email):
    r = _get(f"/users/email_exists/{email}")
    return r.get("exists", False)


def phone_exists(phone):
    r = _get(f"/users/phone_exists/{phone}")
    return r.get("exists", False)


def get_user_email(email):
    try:
        r = _get(f"/users/email/{email}")
        return r.get("email")
    except Exception:
        return None


# -----------------------------------------------------------------------
# Admin
# -----------------------------------------------------------------------

def get_all_users(admin_email):
    r = _get("/admin/users", admin_email=admin_email)
    return r.get("users", [])


def set_user_banned(admin_email, email, banned=True):
    """Returns {"success": bool, "message": str}."""
    return _post("/admin/users/ban", {"admin_email": admin_email, "email": email, "banned": banned})


def create_report(reporter_email, category, offender_type, subject, description, offender_email=""):
    """Returns {"success": bool, "message": str}."""
    return _post("/reports", {"reporter_email": reporter_email, "category": category, "offender_type": offender_type,
                              "subject": subject, "description": description, "offender_email": offender_email})


def get_reports(admin_email):
    r = _get("/admin/reports", admin_email=admin_email)
    return r.get("reports", [])


def resolve_report(admin_email, report_id, resolution="Resolved"):
    return _post(f"/admin/reports/{report_id}/resolve", {"admin_email": admin_email, "resolution": resolution})


# -----------------------------------------------------------------------
# Venues
# -----------------------------------------------------------------------

def get_all_venues():
    r = _get("/venues")
    return r.get("venues", [])


def get_venues_by_vendor(vendor_email):
    r = _get(f"/venues/vendor/{vendor_email}")
    return r.get("venues", [])


def create_venue(name, address, vendor_email, maps_url=""):
    return _post("/venues", {"name": name, "address": address, "vendor_email": vendor_email, "maps_url": maps_url})


def delete_venue(venue_id):
    r = _delete(f"/venues/{venue_id}")
    return r.get("success", False)


# -----------------------------------------------------------------------
# Vendor Categories
# -----------------------------------------------------------------------

def get_vendor_categories(vendor_email):
    r = _get(f"/vendor_categories/{vendor_email}")
    return r.get("categories", [])


def add_vendor_category(vendor_email, name):
    r = _post("/vendor_categories", {"vendor_email": vendor_email, "name": name})
    return r.get("success", False)


def delete_vendor_category(category_id):
    _delete(f"/vendor_categories/{category_id}")


# -----------------------------------------------------------------------
# Events
# -----------------------------------------------------------------------

def get_all_events():
    r = _get("/events")
    return r.get("events", [])


def get_events_by_vendor(vendor_email):
    r = _get(f"/events/vendor/{vendor_email}")
    return r.get("events", [])


def get_events_by_venue(venue_id):
    r = _get(f"/events/venue/{venue_id}")
    return r.get("events", [])


def get_events_today():
    r = _get("/events/today")
    return r.get("events", [])


def create_event(title, category, price, description, vendor_email, venue_id,
                 event_datetime, is_recurring, recur_day, recur_time, capacity=None, image_b64=None):
    return _post("/events", {
        "title": title, "category": category, "price": price,
        "description": description, "vendor_email": vendor_email, "venue_id": venue_id,
        "event_datetime": event_datetime, "is_recurring": is_recurring,
        "recur_day": recur_day, "recur_time": recur_time, "capacity": capacity,
        "image_b64": image_b64,
    })


def update_event(event_id, title, category, price, description, venue_id,
                 event_datetime, is_recurring, recur_day, recur_time, capacity=None,
                 image_b64=None, remove_image=False):
    return _put(f"/events/{event_id}", {
        "title": title, "category": category, "price": price,
        "description": description, "venue_id": venue_id,
        "event_datetime": event_datetime, "is_recurring": is_recurring,
        "recur_day": recur_day, "recur_time": recur_time, "capacity": capacity,
        "image_b64": image_b64, "remove_image": remove_image,
    })


def delete_event(event_id):
    _delete(f"/events/{event_id}")


def get_event_capacity(event_id, booking_date=None):
    params = {}
    if booking_date is not None:
        params["date"] = str(booking_date)
    r = _get(f"/events/{event_id}/capacity", **params)
    return r.get("capacity", {"total": DEFAULT_EVENT_CAPACITY, "source": "event", "vehicles": [], "booked": None, "remaining": None})


def get_event_demand(event_id):
    r = _get(f"/events/{event_id}/demand")
    return r.get("bookings", 0), r.get("guests", 0)


def count_active_bookings(event_id):
    r = _get(f"/events/{event_id}/active_bookings")
    return r.get("count", 0)


def get_event_image(event_id):
    """Picture bytes of an event, or None if the vendor did not add one."""
    try:
        resp = _SESSION.get(f"{BASE_URL}/events/{event_id}/image", timeout=10)
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Cannot connect to the Rihla server. Is it running? (python server/server.py)")
    return resp.content if resp.status_code == 200 else None


# -----------------------------------------------------------------------
# Bookings
# -----------------------------------------------------------------------

def create_booking(customer_email, event_id, booking_date, guests, is_partner=False, client_name=""):
    r = _post("/bookings", {
        "customer_email": customer_email, "event_id": event_id,
        "booking_date": str(booking_date), "guests": guests,
        "is_partner": is_partner, "client_name": client_name,
    })
    return r


def get_bookings_by_customer(customer_email):
    r = _get(f"/bookings/customer/{customer_email}")
    return r.get("bookings", [])


def get_bookings_by_vendor(vendor_email):
    r = _get(f"/bookings/vendor/{vendor_email}")
    return r.get("bookings", [])


def cancel_booking(booking_id, customer_email, reason=""):
    r = _post(f"/bookings/{booking_id}/cancel", {"customer_email": customer_email, "reason": reason})
    return r


def vendor_cancel_booking(booking_id, vendor_email, reason):
    return _post(f"/bookings/{booking_id}/vendor_cancel", {"vendor_email": vendor_email, "reason": reason})


def get_all_bookings(admin_email):
    r = _get("/admin/bookings", admin_email=admin_email)
    return r.get("bookings", [])


def admin_cancel_booking(booking_id, admin_email, reason):
    return _post(f"/admin/bookings/{booking_id}/cancel", {"admin_email": admin_email, "reason": reason})


# -----------------------------------------------------------------------
# Tickets
# -----------------------------------------------------------------------

def verify_ticket_code(ticket_code, expected_event_title=None):
    r = _post("/tickets/verify", {"ticket_code": ticket_code, "expected_event_title": expected_event_title})
    return r


def format_ticket_code(code):
    """Formats '1234567890123456' as '1234 5678 9012 3456'. Pure client-side."""
    code = (code or "").replace(" ", "").strip()
    return " ".join(code[i:i + 4] for i in range(0, len(code), 4)) if len(code) == 16 else code


# -----------------------------------------------------------------------
# Support Tickets
# -----------------------------------------------------------------------

def create_support_ticket(customer_email, subject, message, event_title=""):
    r = _post("/support", {"customer_email": customer_email, "subject": subject, "message": message, "event_title": event_title})
    return r


def get_support_tickets_by_customer(customer_email):
    r = _get(f"/support/customer/{customer_email}")
    return r.get("tickets", [])


def get_open_support_tickets():
    r = _get("/support/open")
    return r.get("tickets", [])


def resolve_support_ticket(ticket_id, staff_email):
    r = _post(f"/support/{ticket_id}/resolve", {"staff_email": staff_email})
    return r.get("success", False)


# -----------------------------------------------------------------------
# Vehicles
# -----------------------------------------------------------------------

def get_vehicle_types():
    r = _get("/vehicle_types")
    return r.get("vehicle_types", [])


def get_vehicle_capacity(vehicle_type):
    types = get_vehicle_types()
    for vt in types:
        if vt["name"] == vehicle_type:
            return vt["capacity"]
    return 4


def get_all_vehicles(dispatcher_email):
    r = _get(f"/vehicles/{dispatcher_email}")
    return r.get("vehicles", [])


def create_vehicle(license_number, vehicle_type, location, dispatcher_email, auto_reassign_recurring):
    r = _post("/vehicles", {
        "license_number": license_number, "vehicle_type": vehicle_type,
        "location": location, "dispatcher_email": dispatcher_email,
        "auto_reassign_recurring": auto_reassign_recurring,
    })
    if not r.get("success", False):
        # Old SQLite code raised IntegrityError (e.g. duplicate license plate); keep that contract for the UI.
        raise ValueError(r.get("message", "Could not create vehicle."))


def delete_vehicle(vehicle_id):
    _delete(f"/vehicles/{vehicle_id}")


def update_vehicle_status(vehicle_id, status):
    _put(f"/vehicles/{vehicle_id}/status", {"status": status})


def free_vehicle(vehicle_id):
    _post(f"/vehicles/{vehicle_id}/free")


# -----------------------------------------------------------------------
# Dispatch
# -----------------------------------------------------------------------

def get_dispatches_by_event(event_id):
    r = _get(f"/dispatch/{event_id}")
    return r.get("dispatches", [])


def dispatch_vehicle_combination(event_id, vehicle_assignments):
    r = _post("/dispatch", {"event_id": event_id, "vehicle_assignments": vehicle_assignments})
    return r.get("assigned", 0)


def get_assigned_vehicles_for_event(event_id):
    r = _get(f"/dispatch/{event_id}/vehicles")
    return r.get("vehicles", [])


# -----------------------------------------------------------------------
# Partner Cart
# -----------------------------------------------------------------------

def get_cart_items(partner_email):
    r = _get(f"/cart/{partner_email}")
    return r.get("items", [])


def get_cart_count(partner_email):
    r = _get(f"/cart/{partner_email}/count")
    return r.get("count", 0)


def add_to_cart(partner_email, event_id, booking_date, guests, client_name=""):
    r = _post("/cart", {
        "partner_email": partner_email, "event_id": event_id,
        "booking_date": str(booking_date), "guests": guests, "client_name": client_name,
    })
    return r


def remove_from_cart(cart_id, partner_email):
    r = _post(f"/cart/{cart_id}/remove", {"partner_email": partner_email})
    return r.get("success", False)


def clear_cart(partner_email):
    _post(f"/cart/{partner_email}/clear")


def checkout_cart(partner_email):
    r = _post(f"/cart/{partner_email}/checkout")
    return r


# -----------------------------------------------------------------------
# Utility (pure helpers that don't need the server)
# -----------------------------------------------------------------------

def price_to_int(price_text):
    """Turns '240 AED' or 240 into the integer 240."""
    digits = "".join(c for c in str(price_text) if c in "0123456789")
    return int(digits) if digits else 0


# -----------------------------------------------------------------------
# Reviews (My Experiences)
# -----------------------------------------------------------------------

def get_my_experiences(customer_email):
    """Past bookings of the customer, each with review_rating and review_comment."""
    r = _get(f"/experiences/customer/{customer_email}")
    return r.get("experiences", [])


def submit_review(customer_email, booking_id, rating, comment=""):
    r = _post("/reviews", {
        "customer_email": customer_email, "booking_id": booking_id,
        "rating": rating, "comment": comment,
    })
    return r


def get_event_ratings():
    """{'3': {'average': 4.5, 'count': 2}, ...} (keys are event ids as text). Events with no reviews are missing."""
    r = _get("/events/ratings")
    return r.get("ratings", {})


def update_venue_maps_url(venue_id, vendor_email, maps_url):
    """Adds, changes or removes (empty text) the Google Maps link of a venue. Returns the server answer."""
    return _put(f"/venues/{venue_id}/maps_url", {"vendor_email": vendor_email, "maps_url": maps_url})
