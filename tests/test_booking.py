import datetime
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "server"))

import db_test_helpers as d
import database_core


def next_weekday(names):
    # At least 3 days ahead, so the booker can still cancel with a full refund.
    day = datetime.date.today() + datetime.timedelta(days=3)
    while day.strftime("%A") not in names:
        day += datetime.timedelta(days=1)
    return day


class BookingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        database_core.DB_PATH = os.path.join(self.tmp.name, "test.db")
        d.init_db()
        self.events = {e["title"]: e for e in d.get_all_events()}
        self.safari = self.events["Red Dune Sunset Safari and Royal BBQ Dinner"]
        self.day = next_weekday(("Tuesday", "Thursday"))

    def tearDown(self):
        self.tmp.cleanup()

    def book(self, email="a@email.com", guests=2, day=None):
        return d.create_booking(email, self.safari["id"], (day or self.day).isoformat(), guests)

    def test_init_twice_keeps_one_demo_booking(self):
        d.init_db()
        self.assertEqual(len(d.get_bookings_by_customer("customer@email.com")), 1)

    def test_booking_price_and_code(self):
        result = self.book(guests=3)
        self.assertTrue(result["success"])
        self.assertEqual(result["booking"]["base_price"], 720)
        self.assertEqual(result["booking"]["vat"], 36)
        self.assertEqual(result["booking"]["total_price"], 756)
        self.assertEqual(len(result["booking"]["ticket_code"]), 16)

    def test_refusals(self):
        self.assertFalse(self.book(day=self.day + datetime.timedelta(days=1))["success"])
        self.assertFalse(self.book(day=datetime.date(2020, 1, 7))["success"])
        self.assertFalse(self.book(guests=0)["success"])
        self.assertFalse(self.book(guests=d.MAX_GUESTS_PER_BOOKING + 1)["success"])
        self.assertFalse(d.create_booking("", self.safari["id"], self.day.isoformat(), 1)["success"])

    def test_customer_can_further_book_same_event(self):
        # A customer can further book the same event if they wish
        res1 = self.book(guests=2)
        self.assertTrue(res1["success"])
        res2 = self.book(guests=3)
        self.assertTrue(res2["success"])
        bookings = d.get_bookings_by_customer("a@email.com")
        self.assertEqual(len(bookings), 2)

    def test_scanner_accepts_once_and_reports_guests(self):
        code = self.book(guests=4)["booking"]["ticket_code"]
        first = d.verify_ticket_code(code, self.safari["title"])
        self.assertTrue(first["success"])
        self.assertIn("Admit 4 guest", first["message"])
        self.assertFalse(d.verify_ticket_code(code)["success"])

    def test_cancel_stops_ticket(self):
        booking = self.book()["booking"]
        self.assertFalse(d.cancel_booking(booking["id"], "other@email.com")["success"])
        self.assertTrue(d.cancel_booking(booking["id"], "a@email.com")["success"])
        self.assertFalse(d.verify_ticket_code(booking["ticket_code"])["success"])

    def test_used_ticket_cannot_be_cancelled(self):
        booking = self.book()["booking"]
        d.verify_ticket_code(booking["ticket_code"])
        self.assertFalse(d.cancel_booking(booking["id"], "a@email.com")["success"])

    def test_rename_then_delete_event(self):
        booking = self.book()["booking"]
        self.assertEqual(d.count_active_bookings(self.safari["id"]), 1)
        d.update_event(self.safari["id"], "Renamed", "Evening Safari", "240 AED", "long description", self.safari["venue_id"],
                       "2026-11-05 15:30", "Recurring", "Tuesday, Thursday", "15:30")
        self.assertIn("Renamed", d.verify_ticket_code(booking["ticket_code"], "Old title")["message"])
        d.delete_event(self.safari["id"])
        self.assertEqual(d.get_bookings_by_customer("a@email.com")[0]["status"], "Cancelled")
        self.assertFalse(d.verify_ticket_code(booking["ticket_code"])["success"])

    def test_vendor_view_and_demand(self):
        self.book(guests=2)
        self.book(email="b@email.com", guests=3)
        rows = d.get_bookings_by_vendor("vendor@email.com")
        self.assertEqual(sum(r["guests"] for r in rows if r["event_title"] == self.safari["title"]), 5)
        self.assertEqual(d.get_event_demand(self.safari["id"]), (2, 5))

    def test_todays_schedule(self):
        today = datetime.date.today()
        d.create_event("Today only", "General", "100 AED", "a long enough description", "vendor@email.com", 1,
                       today.isoformat() + " 18:00", "One-Time", "N/A", "18:00")
        event_id = [e for e in d.get_all_events() if e["title"] == "Today only"][0]["id"]
        result = d.create_booking("a@email.com", event_id, today.isoformat(), 2)
        self.assertTrue(result["success"])
        row = [e for e in d.get_events_today() if e["title"] == "Today only"][0]
        self.assertEqual((row["bookings"], row["guests"], row["checked_in"]), (1, 2, 0))
        d.verify_ticket_code(result["booking"]["ticket_code"])
        row = [e for e in d.get_events_today() if e["title"] == "Today only"][0]
        self.assertEqual(row["checked_in"], 2)

    def test_support_tickets(self):
        title = self.safari["title"]
        self.assertFalse(d.create_support_ticket("a@email.com", "x", "too short", title)["success"])
        for i in range(d.MAX_OPEN_SUPPORT_TICKETS):
            self.assertTrue(d.create_support_ticket("a@email.com", f"Subject {i}", "A message that is long enough", title)["success"])
        self.assertFalse(d.create_support_ticket("a@email.com", "One more", "A message that is long enough", title)["success"])
        open_tickets = d.get_open_support_tickets()
        self.assertEqual(len(open_tickets), d.MAX_OPEN_SUPPORT_TICKETS)
        self.assertEqual(open_tickets[0]["event_title"], title)
        self.assertTrue(d.resolve_support_ticket(open_tickets[0]["id"], "staff@email.com"))
        self.assertFalse(d.resolve_support_ticket(open_tickets[0]["id"], "staff@email.com"))
        statuses = [t["status"] for t in d.get_support_tickets_by_customer("a@email.com")]
        self.assertEqual(statuses.count("Resolved"), 1)

    def test_support_ticket_needs_an_event(self):
        message = "A message that is long enough"
        self.assertFalse(d.create_support_ticket("b@email.com", "Help", message)["success"])
        self.assertFalse(d.create_support_ticket("b@email.com", "Help", message, "Made up event")["success"])
        self.assertTrue(d.create_support_ticket("b@email.com", "Help", message, self.safari["title"])["success"])

    def test_support_ticket_for_booked_event_that_is_no_longer_listed(self):
        message = "A message that is long enough"
        self.assertTrue(self.book()["success"])
        d.delete_event(self.safari["id"])
        self.assertFalse(d.create_support_ticket("b@email.com", "Help", message, self.safari["title"])["success"])
        self.assertTrue(d.create_support_ticket("a@email.com", "Help", message, self.safari["title"])["success"])


class CancellationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        database_core.DB_PATH = os.path.join(self.tmp.name, "test.db")
        d.init_db()

    def tearDown(self):
        self.tmp.cleanup()

    def event_in(self, hours, capacity=10, title="Soon"):
        """A one-time 100 AED event starting the given number of hours from now."""
        start = (datetime.datetime.now() + datetime.timedelta(hours=hours)).replace(second=0, microsecond=0)
        d.create_event(title, "General", "100 AED", "a long enough description", "vendor@email.com", 1,
                       start.strftime("%Y-%m-%d %H:%M"), "One-Time", "N/A", start.strftime("%H:%M"), capacity=capacity)
        event = [e for e in d.get_all_events() if e["title"] == title][0]
        return event, start.date().isoformat()

    def book(self, hours, email="a@email.com", guests=2):
        event, day = self.event_in(hours)
        return d.create_booking(email, event["id"], day, guests)["booking"]

    def booking_row(self, booking_id, email="a@email.com"):
        return [b for b in d.get_bookings_by_customer(email) if b["id"] == booking_id][0]

    def test_refund_policy_steps(self):
        now = datetime.datetime(2030, 1, 10, 12, 0)
        start = datetime.datetime(2030, 1, 12, 12, 0)
        self.assertEqual(d.refund_percent_for(start, now), 100)  # exactly 48h
        self.assertEqual(d.refund_percent_for(start, now + datetime.timedelta(minutes=1)), 50)
        self.assertEqual(d.refund_percent_for(start, now + datetime.timedelta(hours=24)), 50)  # exactly 24h
        self.assertIsNone(d.refund_percent_for(start, now + datetime.timedelta(hours=24, minutes=1)))

    def test_vat_is_refunded_in_proportion(self):
        self.assertEqual(d.split_refund(210, 100), (200, 10, 210))
        self.assertEqual(d.split_refund(210, 50), (100, 5, 105))

    def test_full_refund_and_audit_trail(self):
        booking = self.book(72)
        self.assertTrue(self.booking_row(booking["id"])["can_cancel"])
        result = d.cancel_booking(booking["id"], "a@email.com", "Plans changed")
        self.assertTrue(result["success"])
        self.assertEqual(result["refund"], {"percent": 100, "base": 200, "vat": 10, "total": 210})
        row = self.booking_row(booking["id"])
        self.assertEqual((row["status"], row["refund_percent"], row["refund_amount"]), ("Cancelled", 100, 210))
        self.assertEqual((row["cancelled_by"], row["cancelled_by_role"], row["cancel_reason"]),
                         ("a@email.com", "Customer", "Plans changed"))
        self.assertTrue(row["cancelled_at"])
        self.assertFalse(d.cancel_booking(booking["id"], "a@email.com")["success"])

    def test_half_refund_between_24_and_48_hours(self):
        booking = self.book(30)
        self.assertEqual(self.booking_row(booking["id"])["refund_if_cancelled"], 50)
        result = d.cancel_booking(booking["id"], "a@email.com")
        self.assertEqual(result["refund"]["total"], 105)

    def test_booker_cannot_cancel_in_the_last_24_hours(self):
        booking = self.book(5)
        self.assertFalse(self.booking_row(booking["id"])["can_cancel"])
        result = d.cancel_booking(booking["id"], "a@email.com")
        self.assertFalse(result["success"])
        self.assertIn("24 hours", result["message"])
        self.assertTrue(d.verify_ticket_code(booking["ticket_code"])["success"])

    def test_vendor_cancels_late_with_full_refund_and_a_reason(self):
        booking = self.book(5)
        self.assertFalse(d.vendor_cancel_booking(booking["id"], "vendor@email.com", "")["success"])
        self.assertFalse(d.vendor_cancel_booking(booking["id"], "someone@email.com", "Weather")["success"])
        result = d.vendor_cancel_booking(booking["id"], "vendor@email.com", "Sandstorm warning")
        self.assertTrue(result["success"])
        self.assertEqual(result["refund"]["percent"], 100)
        row = self.booking_row(booking["id"])
        self.assertEqual((row["cancelled_by_role"], row["cancel_reason"]), ("Vendor", "Sandstorm warning"))
        self.assertFalse(d.verify_ticket_code(booking["ticket_code"])["success"])

    def test_nobody_cancels_after_the_start(self):
        event, day = self.event_in(-1, title="Started")
        booking = d.create_booking("a@email.com", event["id"], day, 1)["booking"]
        if booking is None:  # started yesterday (just after midnight): nothing to test
            return
        self.assertFalse(d.vendor_cancel_booking(booking["id"], "vendor@email.com", "Too late")["success"])
        self.assertIn("already started", d.cancel_booking(booking["id"], "a@email.com")["message"])

    def test_only_admins_cancel_any_booking(self):
        booking = self.book(5)
        self.assertIsNone(d.get_all_bookings("vendor@email.com"))
        self.assertFalse(d.admin_cancel_booking(booking["id"], "vendor@email.com", "No")["success"])
        self.assertTrue(any(b["id"] == booking["id"] for b in d.get_all_bookings("admin@email.com")))
        result = d.admin_cancel_booking(booking["id"], "admin@email.com", "Duplicate booking")
        self.assertTrue(result["success"])
        self.assertEqual(self.booking_row(booking["id"])["cancelled_by_role"], "Admin")

    def test_deleting_an_event_refunds_upcoming_bookings(self):
        event, day = self.event_in(72, title="Doomed")
        booking = d.create_booking("a@email.com", event["id"], day, 2)["booking"]
        d.delete_event(event["id"])
        row = self.booking_row(booking["id"])
        self.assertEqual((row["status"], row["refund_amount"], row["cancelled_by"]), ("Cancelled", 210, "vendor@email.com"))

    def test_demand_counts_upcoming_bookings_only(self):
        event, day = self.event_in(72, title="Counted")
        d.create_booking("a@email.com", event["id"], day, 2)
        import sqlite3
        conn = sqlite3.connect(database_core.DB_PATH)
        conn.execute("INSERT INTO tickets (ticket_code, event_title, customer_email, status) VALUES ('1111222233334444', 'Counted', 'b@email.com', 'Valid')")
        conn.execute("INSERT INTO bookings (customer_email, event_id, event_title, booking_date, guests, total_price, ticket_code, status) "
                     "VALUES ('b@email.com', ?, 'Counted', '2020-01-01', 5, 525, '1111222233334444', 'Confirmed')", (event["id"],))
        conn.commit()
        conn.close()
        self.assertEqual(d.get_event_demand(event["id"]), (1, 2))
        self.assertEqual(d.count_active_bookings(event["id"]), 1)

    def test_failed_cart_checkout_keeps_no_bookings(self):
        event, day = self.event_in(72, capacity=5, title="Small")
        self.assertTrue(d.add_to_cart("partner@email.com", event["id"], day, 3)["success"])
        self.assertTrue(d.add_to_cart("partner@email.com", event["id"], day, 3)["success"])
        result = d.checkout_cart("partner@email.com")
        self.assertFalse(result["success"])
        self.assertIn("payment was not taken", result["message"])
        self.assertEqual(d.get_bookings_by_customer("partner@email.com"), [])
        self.assertEqual(d.get_cart_count("partner@email.com"), 2)
        self.assertEqual(d.get_event_capacity(event["id"], day)["remaining"], 5)


class CapacityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        database_core.DB_PATH = os.path.join(self.tmp.name, "test.db")
        d.init_db()
        self.day = datetime.date.today() + datetime.timedelta(days=3)
        d.create_event("Small dinner", "General", "100 AED", "a long enough description", "vendor@email.com", 1,
                       self.day.isoformat() + " 19:00", "One-Time", "N/A", "19:00", capacity=5)
        self.dinner = [e for e in d.get_all_events() if e["title"] == "Small dinner"][0]

    def tearDown(self):
        self.tmp.cleanup()

    def book(self, email, guests, event=None, day=None):
        return d.create_booking(email, (event or self.dinner)["id"], (day or self.day).isoformat(), guests)

    def assign(self, event_id, vehicle_type, how_many):
        fleet = [v for v in d.get_all_vehicles("dispatcher@email.com") if v["vehicle_type"] == vehicle_type and v["status"] == "Available"]
        chosen = fleet[:how_many]
        self.assertEqual(len(chosen), how_many)
        d.dispatch_vehicle_combination(event_id, [{"vehicle_id": v["id"], "auto_reassign_recurring": 0} for v in chosen])

    def test_event_without_vehicles_uses_its_own_capacity(self):
        info = d.get_event_capacity(self.dinner["id"], self.day)
        self.assertEqual((info["total"], info["source"], info["vehicles"]), (5, "event", []))
        self.assertEqual((info["booked"], info["remaining"]), (0, 5))

    def test_cannot_book_more_than_capacity(self):
        self.assertTrue(self.book("a@email.com", 3)["success"])
        too_many = self.book("b@email.com", 3)
        self.assertFalse(too_many["success"])
        self.assertIn("Only 2 of 5 seats", too_many["message"])
        self.assertTrue(self.book("b@email.com", 2)["success"])
        full = self.book("c@email.com", 1)
        self.assertFalse(full["success"])
        self.assertIn("fully booked", full["message"])
        self.assertEqual(d.get_event_capacity(self.dinner["id"], self.day)["remaining"], 0)

    def test_one_booking_cannot_be_larger_than_the_whole_event(self):
        self.assertFalse(self.book("a@email.com", 6)["success"])
        self.assertTrue(self.book("a@email.com", 5)["success"])

    def test_cancelling_frees_the_seats(self):
        booking = self.book("a@email.com", 5)["booking"]
        self.assertFalse(self.book("b@email.com", 1)["success"])
        d.cancel_booking(booking["id"], "a@email.com")
        self.assertEqual(d.get_event_capacity(self.dinner["id"], self.day)["remaining"], 5)
        self.assertTrue(self.book("b@email.com", 1)["success"])

    def test_capacity_counts_each_date_on_its_own(self):
        d.create_event("Daily tour", "General", "50 AED", "a long enough description", "vendor@email.com", 1,
                       self.day.isoformat() + " 09:00", "Recurring",
                       "Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday", "09:00", capacity=2)
        tour = [e for e in d.get_all_events() if e["title"] == "Daily tour"][0]
        next_day = self.day + datetime.timedelta(days=1)
        self.assertTrue(self.book("a@email.com", 2, tour)["success"])
        self.assertFalse(self.book("b@email.com", 1, tour)["success"])
        self.assertTrue(self.book("b@email.com", 1, tour, next_day)["success"])

    def test_vehicle_combination_sets_the_capacity(self):
        self.assign(self.dinner["id"], "desert buggy", 1)
        self.assign(self.dinner["id"], "4x4 toyota landcrusier", 1)
        info = d.get_event_capacity(self.dinner["id"])
        self.assertEqual((info["total"], info["source"]), (8, "vehicles"))
        self.assertEqual(sorted((v["vehicle_type"], v["count"], v["seats_each"]) for v in info["vehicles"]),
                         [("4x4 toyota landcrusier", 1, 6), ("desert buggy", 1, 2)])
        self.assertTrue(self.book("a@email.com", 6)["success"])
        self.assertFalse(self.book("b@email.com", 3)["success"])
        self.assertTrue(self.book("b@email.com", 2)["success"])

    def test_two_vehicles_of_the_same_type_add_up(self):
        self.assign(self.dinner["id"], "desert buggy", 2)
        self.assertEqual(d.get_event_capacity(self.dinner["id"])["total"], 4)

    def test_freeing_a_vehicle_goes_back_to_vendor_capacity(self):
        self.assign(self.dinner["id"], "RTA bus", 1)
        self.assertEqual(d.get_event_capacity(self.dinner["id"])["total"], 50)
        bus = [v for v in d.get_all_vehicles("dispatcher@email.com") if v["vehicle_type"] == "RTA bus"][0]
        d.free_vehicle(bus["id"])
        info = d.get_event_capacity(self.dinner["id"])
        self.assertEqual((info["total"], info["source"]), (5, "event"))

    def test_setting_available_releases_the_vehicle_from_its_event(self):
        self.assign(self.dinner["id"], "RTA bus", 1)
        bus = [v for v in d.get_all_vehicles("dispatcher@email.com") if v["vehicle_type"] == "RTA bus"][0]
        self.assertEqual(len(d.get_dispatches_by_event(self.dinner["id"])), 1)
        d.update_vehicle_status(bus["id"], "Available")
        self.assertEqual(d.get_dispatches_by_event(self.dinner["id"]), [])
        bus = [v for v in d.get_all_vehicles("dispatcher@email.com") if v["id"] == bus["id"]][0]
        self.assertEqual(bus["status"], "Available")
        self.assertEqual(d.get_event_capacity(self.dinner["id"])["source"], "event")

    def test_edit_event_capacity(self):
        e = self.dinner
        d.update_event(e["id"], e["title"], e["category"], e["price"], e["desc"], e["venue_id"], e["event_datetime"],
                       e["is_recurring"], e["recur_day"], e["recur_time"], capacity=8)
        self.assertEqual(d.get_event_capacity(e["id"])["total"], 8)
        # No capacity given: the event keeps the one it has.
        d.update_event(e["id"], e["title"], e["category"], e["price"], e["desc"], e["venue_id"], e["event_datetime"],
                       e["is_recurring"], e["recur_day"], e["recur_time"])
        self.assertEqual(d.get_event_capacity(e["id"])["total"], 8)

    def test_bad_capacity_is_rejected(self):
        for bad in (0, -3, d.MAX_EVENT_CAPACITY + 1):
            with self.assertRaises(ValueError):
                d.create_event("Bad", "General", "10 AED", "a long enough description", "vendor@email.com", 1,
                               "2030-01-01 10:00", "One-Time", "N/A", "10:00", capacity=bad)

    def test_demo_events_have_capacity(self):
        titles = {e["title"]: e["capacity"] for e in d.get_all_events()}
        self.assertEqual(titles["New year dinner"], 40)
        self.assertEqual(titles["Red Dune Sunset Safari and Royal BBQ Dinner"], 30)

    def test_old_database_gets_the_capacity_column(self):
        import sqlite3
        old_path = os.path.join(self.tmp.name, "old.db")
        conn = sqlite3.connect(old_path)
        conn.execute("CREATE TABLE events (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, category TEXT, price TEXT, "
                     "description TEXT, vendor_email TEXT, venue_id INTEGER, event_datetime TEXT, is_recurring TEXT, recur_day TEXT, recur_time TEXT)")
        conn.execute("INSERT INTO events (title, price, event_datetime, is_recurring) VALUES ('Old event', '10 AED', '2030-01-01 10:00', 'One-Time')")
        conn.commit()
        conn.close()
        database_core.DB_PATH = old_path
        d.init_db()
        d.init_db()
        old_event = [e for e in d.get_all_events() if e["title"] == "Old event"][0]
        self.assertEqual(old_event["capacity"], d.DEFAULT_EVENT_CAPACITY)


if __name__ == "__main__":
    unittest.main()
