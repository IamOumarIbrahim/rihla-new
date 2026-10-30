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


class CapacityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d.DB_PATH = os.path.join(self.tmp.name, "test.db")
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
        d.DB_PATH = old_path
        d.init_db()
        d.init_db()
        old_event = [e for e in d.get_all_events() if e["title"] == "Old event"][0]
        self.assertEqual(old_event["capacity"], d.DEFAULT_EVENT_CAPACITY)


if __name__ == "__main__":
    unittest.main()
