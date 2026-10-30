"""
tests/db_test_helpers.py

For tests only: imports directly from the server-side database modules
(bypassing the HTTP API) so tests remain fast, isolated, and don't require
a running server.  Both test files do:
    import db_test_helpers as d
instead of `import database as d`.
"""
import sys
import os

# Point to server/ modules
_SERVER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server"))
if _SERVER_DIR not in sys.path:
    sys.path.insert(0, _SERVER_DIR)

from database_core import (
    init_db, register_user, check_login, get_role, get_user_email,
    update_password, email_exists, phone_exists,
    create_support_ticket, get_support_tickets_by_customer,
    get_open_support_tickets, resolve_support_ticket,
    DB_PATH, DEFAULT_EVENT_CAPACITY, MAX_EVENT_CAPACITY,
    MAX_GUESTS_PER_BOOKING, MAX_OPEN_SUPPORT_TICKETS,
)

from database_events import (
    get_all_venues, get_venues_by_vendor, create_venue, delete_venue,
    get_vendor_categories, add_vendor_category, delete_vendor_category,
    get_all_events, get_events_by_vendor, get_events_by_venue, get_events_today,
    create_event, update_event, delete_event,
    get_event_capacity, get_event_demand, count_active_bookings,
    create_booking, get_bookings_by_customer, get_bookings_by_vendor, cancel_booking,
    vendor_cancel_booking, admin_cancel_booking, get_all_bookings, refund_percent_for, split_refund,
    verify_ticket_code, format_ticket_code, price_to_int,
    get_vehicle_types, get_vehicle_capacity, get_all_vehicles,
    create_vehicle, delete_vehicle, update_vehicle_status, free_vehicle,
    get_dispatches_by_event, dispatch_vehicle_combination,
    get_cart_items, get_cart_count, add_to_cart, remove_from_cart,
    clear_cart, checkout_cart,
)
