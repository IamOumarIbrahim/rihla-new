import datetime
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import database as d


def next_weekday(names):
    day = datetime.date.today()
    while day.strftime("%A") not in names:
        day += datetime.timedelta(days=1)
    return day


class BookingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d.DB_PATH = os.path.join(self.tmp.name, "test.db")
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
        self.assertEqual(result["booking"]["total_price"], 720)
        self.assertEqual(len(result["booking"]["ticket_code"]), 16)

    def test_refusals(self):
        self.assertFalse(self.book(day=self.day + datetime.timedelta(days=1))["success"])
        self.assertFalse(self.book(day=datetime.date(2020, 1, 7))["success"])
        self.assertFalse(self.book(guests=0)["success"])
        self.assertFalse(self.book(guests=d.MAX_GUESTS_PER_BOOKING + 1)["success"])
        self.assertFalse(d.create_booking("", self.safari["id"], self.day.isoformat(), 1)["success"])

    def test_no_double_booking_same_day(self):
        self.assertTrue(self.book()["success"])
        self.assertFalse(self.book()["success"])

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
        self.assertFalse(d.create_support_ticket("a@email.com", "x", "too short")["success"])
        for i in range(d.MAX_OPEN_SUPPORT_TICKETS):
            self.assertTrue(d.create_support_ticket("a@email.com", f"Subject {i}", "A message that is long enough")["success"])
        self.assertFalse(d.create_support_ticket("a@email.com", "One more", "A message that is long enough")["success"])
        open_tickets = d.get_open_support_tickets()
        self.assertEqual(len(open_tickets), d.MAX_OPEN_SUPPORT_TICKETS)
        self.assertTrue(d.resolve_support_ticket(open_tickets[0]["id"], "staff@email.com"))
        self.assertFalse(d.resolve_support_ticket(open_tickets[0]["id"], "staff@email.com"))
        statuses = [t["status"] for t in d.get_support_tickets_by_customer("a@email.com")]
        self.assertEqual(statuses.count("Resolved"), 1)


if __name__ == "__main__":
    unittest.main()
