"""
Rihla API Server – localhost Flask REST API
Run: python server/server.py
Serves on http://localhost:5000
All data lives in server/users.db (the single source of truth).
"""

import os
import sys

# Make sure server/ modules resolve correctly when run from any cwd
_SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
if _SERVER_DIR not in sys.path:
    sys.path.insert(0, _SERVER_DIR)

from flask import Flask, request, jsonify
import database_core as core
import database_events as events

app = Flask(__name__)

# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

def _ok(data=None, **kwargs):
    payload = {"success": True}
    if data is not None:
        payload.update(data if isinstance(data, dict) else {"data": data})
    payload.update(kwargs)
    return jsonify(payload), 200


def _err(message, status=400):
    return jsonify({"success": False, "message": message}), status


# -----------------------------------------------------------------------
# Auth
# -----------------------------------------------------------------------

@app.route("/api/auth/login", methods=["POST"])
def login():
    body = request.get_json(silent=True) or {}
    email = body.get("email", "")
    password = body.get("password", "")
    if core.check_login(email, password):
        return _ok({"email": core.get_user_email(email) or email, "role": core.get_role(email)})
    return _err("Invalid email or password.", 401)


@app.route("/api/auth/role/<path:email>")
def get_role(email):
    return _ok({"role": core.get_role(email)})


# -----------------------------------------------------------------------
# Users
# -----------------------------------------------------------------------

@app.route("/api/users/register", methods=["POST"])
def register():
    body = request.get_json(silent=True) or {}
    ok = core.register_user(body.get("email", ""), body.get("password", ""),
                            body.get("role", "Customer"), body.get("phone"))
    if ok:
        return _ok({"message": "Registered."})
    return _err("Registration failed – email already exists or invalid data.")


@app.route("/api/users/password", methods=["PUT"])
def update_password():
    body = request.get_json(silent=True) or {}
    core.update_password(body.get("email", ""), body.get("new_password", ""))
    return _ok({"message": "Password updated."})


@app.route("/api/users/email_exists/<path:email>")
def email_exists(email):
    return _ok({"exists": core.email_exists(email)})


@app.route("/api/users/phone_exists/<path:phone>")
def phone_exists(phone):
    return _ok({"exists": core.phone_exists(phone)})


@app.route("/api/users/email/<path:email>")
def get_user_email(email):
    stored = core.get_user_email(email)
    if stored:
        return _ok({"email": stored})
    return _err("Not found.", 404)


# -----------------------------------------------------------------------
# Venues
# -----------------------------------------------------------------------

@app.route("/api/venues")
def get_venues():
    return _ok({"venues": events.get_all_venues()})


@app.route("/api/venues/vendor/<path:vendor_email>")
def get_venues_by_vendor(vendor_email):
    return _ok({"venues": events.get_venues_by_vendor(vendor_email)})


@app.route("/api/venues", methods=["POST"])
def create_venue():
    body = request.get_json(silent=True) or {}
    events.create_venue(body.get("name", ""), body.get("address", ""), body.get("vendor_email", ""))
    return _ok({"message": "Venue created."})


@app.route("/api/venues/<int:venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    ok = events.delete_venue(venue_id)
    if ok:
        return _ok({"message": "Deleted."})
    return _err("Venue is in use by events and cannot be deleted.")


# -----------------------------------------------------------------------
# Vendor Categories
# -----------------------------------------------------------------------

@app.route("/api/vendor_categories/<path:vendor_email>")
def get_vendor_categories(vendor_email):
    return _ok({"categories": events.get_vendor_categories(vendor_email)})


@app.route("/api/vendor_categories", methods=["POST"])
def add_vendor_category():
    body = request.get_json(silent=True) or {}
    ok = events.add_vendor_category(body.get("vendor_email", ""), body.get("name", ""))
    if ok:
        return _ok({"message": "Category added."})
    return _err("Duplicate category name.")


@app.route("/api/vendor_categories/<int:category_id>", methods=["DELETE"])
def delete_vendor_category(category_id):
    events.delete_vendor_category(category_id)
    return _ok({"message": "Deleted."})


# -----------------------------------------------------------------------
# Events
# -----------------------------------------------------------------------

@app.route("/api/events")
def get_all_events():
    return _ok({"events": events.get_all_events()})


@app.route("/api/events/vendor/<path:vendor_email>")
def get_events_by_vendor(vendor_email):
    return _ok({"events": events.get_events_by_vendor(vendor_email)})


@app.route("/api/events/venue/<int:venue_id>")
def get_events_by_venue(venue_id):
    return _ok({"events": events.get_events_by_venue(venue_id)})


@app.route("/api/events/today")
def get_events_today():
    return _ok({"events": events.get_events_today()})


@app.route("/api/events", methods=["POST"])
def create_event():
    body = request.get_json(silent=True) or {}
    try:
        events.create_event(
            body["title"], body.get("category"), body.get("price"),
            body.get("description"), body.get("vendor_email"), body.get("venue_id"),
            body.get("event_datetime"), body.get("is_recurring"), body.get("recur_day"),
            body.get("recur_time"), body.get("capacity")
        )
        return _ok({"message": "Event created."})
    except Exception as e:
        return _err(str(e))


@app.route("/api/events/<int:event_id>", methods=["PUT"])
def update_event(event_id):
    body = request.get_json(silent=True) or {}
    try:
        events.update_event(
            event_id, body["title"], body.get("category"), body.get("price"),
            body.get("description"), body.get("venue_id"), body.get("event_datetime"),
            body.get("is_recurring"), body.get("recur_day"), body.get("recur_time"),
            body.get("capacity")
        )
        return _ok({"message": "Event updated."})
    except Exception as e:
        return _err(str(e))


@app.route("/api/events/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    events.delete_event(event_id)
    return _ok({"message": "Deleted."})


@app.route("/api/events/<int:event_id>/capacity")
def get_event_capacity(event_id):
    date_str = request.args.get("date")
    return _ok({"capacity": events.get_event_capacity(event_id, date_str)})


@app.route("/api/events/<int:event_id>/demand")
def get_event_demand(event_id):
    count, guests = events.get_event_demand(event_id)
    return _ok({"bookings": count, "guests": guests})


@app.route("/api/events/<int:event_id>/active_bookings")
def count_active_bookings(event_id):
    return _ok({"count": events.count_active_bookings(event_id)})


# -----------------------------------------------------------------------
# Bookings
# -----------------------------------------------------------------------

@app.route("/api/bookings", methods=["POST"])
def create_booking():
    body = request.get_json(silent=True) or {}
    result = events.create_booking(
        body.get("customer_email", ""), body.get("event_id"),
        body.get("booking_date"), body.get("guests", 1),
        body.get("is_partner", False), body.get("client_name", "")
    )
    if result["success"]:
        return _ok(result)
    return _err(result["message"])


@app.route("/api/bookings/customer/<path:email>")
def get_bookings_by_customer(email):
    return _ok({"bookings": events.get_bookings_by_customer(email)})


@app.route("/api/bookings/vendor/<path:vendor_email>")
def get_bookings_by_vendor(vendor_email):
    return _ok({"bookings": events.get_bookings_by_vendor(vendor_email)})


@app.route("/api/bookings/<int:booking_id>/cancel", methods=["POST"])
def cancel_booking(booking_id):
    body = request.get_json(silent=True) or {}
    result = events.cancel_booking(booking_id, body.get("customer_email", ""))
    if result["success"]:
        return _ok(result)
    return _err(result["message"])


# -----------------------------------------------------------------------
# Tickets
# -----------------------------------------------------------------------

@app.route("/api/tickets/verify", methods=["POST"])
def verify_ticket():
    body = request.get_json(silent=True) or {}
    result = events.verify_ticket_code(body.get("ticket_code", ""), body.get("expected_event_title"))
    if result["success"]:
        return _ok(result)
    return _err(result["message"])


# -----------------------------------------------------------------------
# Support Tickets
# -----------------------------------------------------------------------

@app.route("/api/support", methods=["POST"])
def create_support_ticket():
    body = request.get_json(silent=True) or {}
    result = core.create_support_ticket(
        body.get("customer_email", ""), body.get("subject", ""), body.get("message", "")
    )
    if result["success"]:
        return _ok(result)
    return _err(result["message"])


@app.route("/api/support/customer/<path:email>")
def get_support_tickets_by_customer(email):
    return _ok({"tickets": core.get_support_tickets_by_customer(email)})


@app.route("/api/support/open")
def get_open_support_tickets():
    return _ok({"tickets": core.get_open_support_tickets()})


@app.route("/api/support/<int:ticket_id>/resolve", methods=["POST"])
def resolve_support_ticket(ticket_id):
    body = request.get_json(silent=True) or {}
    ok = core.resolve_support_ticket(ticket_id, body.get("staff_email", ""))
    if ok:
        return _ok({"message": "Resolved."})
    return _err("Could not resolve (already resolved or not found).")


# -----------------------------------------------------------------------
# Vehicles
# -----------------------------------------------------------------------

@app.route("/api/vehicle_types")
def get_vehicle_types():
    return _ok({"vehicle_types": events.get_vehicle_types()})


@app.route("/api/vehicles/<path:dispatcher_email>")
def get_all_vehicles(dispatcher_email):
    return _ok({"vehicles": events.get_all_vehicles(dispatcher_email)})


@app.route("/api/vehicles", methods=["POST"])
def create_vehicle():
    body = request.get_json(silent=True) or {}
    try:
        events.create_vehicle(
            body["license_number"], body["vehicle_type"], body["location"],
            body["dispatcher_email"], body.get("auto_reassign_recurring", 0)
        )
        return _ok({"message": "Vehicle created."})
    except Exception as e:
        return _err(str(e))


@app.route("/api/vehicles/<int:vehicle_id>", methods=["DELETE"])
def delete_vehicle(vehicle_id):
    events.delete_vehicle(vehicle_id)
    return _ok({"message": "Deleted."})


@app.route("/api/vehicles/<int:vehicle_id>/status", methods=["PUT"])
def update_vehicle_status(vehicle_id):
    body = request.get_json(silent=True) or {}
    events.update_vehicle_status(vehicle_id, body.get("status", "Available"))
    return _ok({"message": "Status updated."})


@app.route("/api/vehicles/<int:vehicle_id>/free", methods=["POST"])
def free_vehicle(vehicle_id):
    events.free_vehicle(vehicle_id)
    return _ok({"message": "Vehicle freed."})


# -----------------------------------------------------------------------
# Dispatch
# -----------------------------------------------------------------------

@app.route("/api/dispatch/<int:event_id>")
def get_dispatches_by_event(event_id):
    return _ok({"dispatches": events.get_dispatches_by_event(event_id)})


@app.route("/api/dispatch", methods=["POST"])
def dispatch_vehicles():
    body = request.get_json(silent=True) or {}
    count = events.dispatch_vehicle_combination(body.get("event_id"), body.get("vehicle_assignments", []))
    return _ok({"assigned": count})


# -----------------------------------------------------------------------
# Partner Cart
# -----------------------------------------------------------------------

@app.route("/api/cart/<path:partner_email>")
def get_cart_items(partner_email):
    return _ok({"items": events.get_cart_items(partner_email)})


@app.route("/api/cart/<path:partner_email>/count")
def get_cart_count(partner_email):
    return _ok({"count": events.get_cart_count(partner_email)})


@app.route("/api/cart", methods=["POST"])
def add_to_cart():
    body = request.get_json(silent=True) or {}
    result = events.add_to_cart(
        body.get("partner_email", ""), body.get("event_id"),
        body.get("booking_date"), body.get("guests", 1), body.get("client_name", "")
    )
    if result["success"]:
        return _ok(result)
    return _err(result["message"])


@app.route("/api/cart/<int:cart_id>/remove", methods=["POST"])
def remove_from_cart(cart_id):
    body = request.get_json(silent=True) or {}
    ok = events.remove_from_cart(cart_id, body.get("partner_email", ""))
    if ok:
        return _ok({"message": "Removed."})
    return _err("Item not found.")


@app.route("/api/cart/<path:partner_email>/clear", methods=["POST"])
def clear_cart(partner_email):
    events.clear_cart(partner_email)
    return _ok({"message": "Cart cleared."})


@app.route("/api/cart/<path:partner_email>/checkout", methods=["POST"])
def checkout_cart(partner_email):
    result = events.checkout_cart(partner_email)
    if result["success"]:
        return _ok(result)
    return _err(result["message"])


# -----------------------------------------------------------------------
# Boot
# -----------------------------------------------------------------------

if __name__ == "__main__":
    core.init_db()
    print("Rihla API server running at http://localhost:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
