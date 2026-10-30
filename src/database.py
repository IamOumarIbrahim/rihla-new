"""
database.py – backward-compatibility shim.

All data access now goes through the Rihla API server (localhost:5000).
This module re-exports everything from api_client so existing imports
(``from database import check_login``) continue to work without changes.
"""
from api_client import *  # noqa: F401, F403
from api_client import (  # explicit re-exports for IDE support
    check_login, get_role, get_user_email,
    register_user, update_password, email_exists, phone_exists,
    get_all_venues, get_venues_by_vendor, create_venue, delete_venue,
    get_vendor_categories, add_vendor_category, delete_vendor_category,
    get_all_events, get_events_by_vendor, get_events_by_venue, get_events_today,
    create_event, update_event, delete_event,
    get_event_capacity, get_event_demand, count_active_bookings,
    create_booking, get_bookings_by_customer, get_bookings_by_vendor, cancel_booking,
    verify_ticket_code, format_ticket_code,
    create_support_ticket, get_support_tickets_by_customer,
    get_open_support_tickets, resolve_support_ticket,
    get_vehicle_types, get_vehicle_capacity, get_all_vehicles,
    create_vehicle, delete_vehicle, update_vehicle_status, free_vehicle,
    get_dispatches_by_event, dispatch_vehicle_combination,
    get_cart_items, get_cart_count, add_to_cart, remove_from_cart,
    clear_cart, checkout_cart,
    price_to_int,
    DEFAULT_EVENT_CAPACITY, MAX_EVENT_CAPACITY,
    MAX_GUESTS_PER_BOOKING, MAX_OPEN_SUPPORT_TICKETS,
)
