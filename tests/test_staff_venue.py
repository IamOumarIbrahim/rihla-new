import datetime
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "server"))

import database_core as core
import database_events as ev
import server

ADMIN = "admin@email.com"
STAFF = "staff@email.com"
SSN = "4000100020009999"


class StaffVenueTests(unittest.TestCase):
    """Staff work at one venue: sign-up, settings, check-in and the schedule all follow it."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        core.DB_PATH = os.path.join(self.tmp.name, "test.db")
        core.init_db()
        venues = {v["name"]: v["id"] for v in ev.get_all_venues()}
        self.burj = venues["Burj Khalifa"]
        self.desert = venues["Dubai Desert Conservation Reserve"]
        # A one-time event today at each venue, each with a booking, so both schedules have something to show.
        today = datetime.date.today().isoformat()
        self.codes = {}
        for venue_id, title in ((self.burj, "Sky lounge tonight"), (self.desert, "Desert dinner tonight")):
            ev.create_event(title, "General", "100 AED", "a long enough description", "vendor@email.com", venue_id,
                            today + " 23:00", "One-Time", "N/A", "23:00")
            event_id = [e for e in ev.get_all_events() if e["title"] == title][0]["id"]
            self.codes[venue_id] = ev.create_booking("guest@email.com", event_id, today, 2)["booking"]["ticket_code"]
        self.client = server.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def register_staff(self, email="new.staff@email.com", venue_id=None, manager="boss@venue.ae"):
        return core.register_user(email, "password123", "Staff", ssn=SSN, venue_id=venue_id, manager_email=manager)

    def test_demo_staff_is_backfilled_with_the_demo_ticket_venue(self):
        venue = core.get_staff_venue(STAFF)
        self.assertEqual(venue["id"], self.burj)
        self.assertEqual(venue["manager_email"], "manager.burjkhalifa@email.com")
        self.assertIsNone(core.get_staff_venue("vendor@email.com"))

    def test_staff_sign_up_needs_an_existing_venue_and_a_manager_email(self):
        self.assertFalse(self.register_staff(venue_id=None))
        self.assertFalse(self.register_staff(venue_id=9999))
        self.assertFalse(self.register_staff(venue_id=self.desert, manager="not-an-email"))
        self.assertFalse(self.register_staff(venue_id=self.desert, manager=""))
        self.assertTrue(self.register_staff(venue_id=self.desert))
        self.assertEqual(core.get_staff_venue("new.staff@email.com")["id"], self.desert)
        # Other roles never keep a venue, even if one is sent.
        core.register_user("v2@email.com", "password123", "Vendor", ssn=SSN, venue_id=self.desert, manager_email="a@b.ae")
        self.assertIsNone(core.get_staff_venue("v2@email.com"))

    def test_sign_up_endpoint_explains_a_missing_venue(self):
        r = self.client.post("/api/users/register", json={"email": "x@email.com", "password": "password123",
                                                           "role": "Staff", "ssn": SSN, "manager_email": "m@v.ae"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("venue", r.get_json()["message"])

    def test_staff_cannot_check_in_another_venues_ticket(self):
        refused = ev.staff_verify_ticket(STAFF, self.codes[self.desert])
        self.assertFalse(refused["success"])
        self.assertIn("not for an event at your venue", refused["message"])
        self.assertNotIn("Desert", refused["message"])  # nothing about the other venue leaks
        # The refused ticket is still valid for the staff at its own venue.
        self.register_staff(venue_id=self.desert)
        self.assertTrue(ev.staff_verify_ticket("new.staff@email.com", self.codes[self.desert])["success"])
        self.assertTrue(ev.staff_verify_ticket(STAFF, self.codes[self.burj])["success"])

    def test_demo_ticket_works_for_demo_staff_only(self):
        self.register_staff(venue_id=self.desert)
        refused = ev.staff_verify_ticket("new.staff@email.com", "1234567890123456")
        self.assertIn("not for an event at your venue", refused["message"])
        self.assertTrue(ev.staff_verify_ticket(STAFF, "1234567890123456", "New year dinner")["success"])

    def test_only_staff_can_use_the_scanner_endpoint(self):
        body = {"ticket_code": self.codes[self.burj]}
        self.assertEqual(self.client.post("/api/tickets/verify", json=body).status_code, 400)
        self.assertEqual(self.client.post("/api/tickets/verify", json={**body, "staff_email": "customer@email.com"}).status_code, 400)
        r = self.client.post("/api/tickets/verify", json={**body, "staff_email": STAFF, "ticket_code": self.codes[self.desert]})
        self.assertFalse(r.get_json()["success"])
        r = self.client.post("/api/tickets/verify", json={**body, "staff_email": STAFF})
        self.assertTrue(r.get_json()["success"])

    def test_schedule_shows_only_the_staff_venue(self):
        r = self.client.get("/api/events/today", query_string={"staff_email": STAFF})
        titles = {e["title"] for e in r.get_json()["events"]}
        self.assertIn("Sky lounge tonight", titles)
        self.assertNotIn("Desert dinner tonight", titles)
        self.assertEqual(self.client.get("/api/events/today").status_code, 403)
        self.assertEqual(self.client.get("/api/events/today", query_string={"staff_email": "vendor@email.com"}).status_code, 403)

    def test_changing_venue_in_settings_moves_check_in_and_schedule(self):
        self.assertFalse(core.set_staff_venue(STAFF, 9999, "m@v.ae")["success"])
        self.assertFalse(core.set_staff_venue(STAFF, self.desert, "bad email")["success"])
        self.assertFalse(core.set_staff_venue("vendor@email.com", self.desert, "m@v.ae")["success"])
        r = self.client.put("/api/staff/venue", json={"email": STAFF, "venue_id": self.desert, "manager_email": "lead@desert.ae"})
        self.assertTrue(r.get_json()["success"])
        self.assertEqual(core.get_staff_venue(STAFF)["manager_email"], "lead@desert.ae")
        self.assertFalse(ev.staff_verify_ticket(STAFF, self.codes[self.burj])["success"])
        self.assertEqual({e["title"] for e in ev.get_staff_schedule(STAFF)}, {"Desert dinner tonight"})
        self.assertTrue(ev.staff_verify_ticket(STAFF, self.codes[self.desert])["success"])

    def test_banned_staff_lose_venue_access(self):
        core.set_user_banned(ADMIN, STAFF, True)
        self.assertFalse(ev.staff_verify_ticket(STAFF, self.codes[self.burj])["success"])
        self.assertIsNone(ev.get_staff_schedule(STAFF))

    def test_venue_with_staff_cannot_be_deleted(self):
        ev.create_venue("Empty hall", "Somewhere", "vendor@email.com")
        hall = [v["id"] for v in ev.get_all_venues() if v["name"] == "Empty hall"][0]
        core.set_staff_venue(STAFF, hall, "m@v.ae")
        self.assertFalse(ev.delete_venue(hall))
        core.set_staff_venue(STAFF, self.burj, "m@v.ae")
        self.assertTrue(ev.delete_venue(hall))

    def test_admin_user_list_shows_venue_and_manager_for_staff_only(self):
        users = {u["email"]: u for u in core.get_all_users(ADMIN)}
        self.assertEqual(users[STAFF]["venue_name"], "Burj Khalifa")
        self.assertEqual(users[STAFF]["manager_email"], "manager.burjkhalifa@email.com")
        self.assertEqual((users["customer@email.com"]["venue_name"], users["customer@email.com"]["manager_email"]), ("", ""))

    def test_support_tickets_are_scoped_to_the_staff_venue(self):
        message = "A message that is long enough"
        core.create_support_ticket("a@email.com", "Burj question", message, "Sky lounge tonight")
        core.create_support_ticket("a@email.com", "Desert question", message, "Desert dinner tonight")
        with core._connect() as conn:  # an old ticket from before tickets had to name an event
            conn.execute("INSERT INTO support_tickets (customer_email, subject, message) VALUES ('old@email.com', 'General', 'Hi')")
        tickets = {t["subject"]: t["id"] for t in core.get_open_support_tickets()}

        r = self.client.get("/api/support/open", query_string={"staff_email": STAFF})
        self.assertEqual({t["subject"] for t in r.get_json()["tickets"]}, {"Burj question", "General"})
        self.assertEqual(self.client.get("/api/support/open").status_code, 403)
        self.assertEqual(self.client.get("/api/support/open", query_string={"staff_email": "customer@email.com"}).status_code, 403)

        # Another venue's ticket cannot be resolved, even by calling the API directly.
        r = self.client.post(f"/api/support/{tickets['Desert question']}/resolve", json={"staff_email": STAFF})
        self.assertFalse(r.get_json()["success"])
        self.assertFalse(core.staff_resolve_support_ticket(tickets["Desert question"], "vendor@email.com"))
        self.assertTrue(core.staff_resolve_support_ticket(tickets["Burj question"], STAFF))

        # After moving venue the staff member sees the desert ticket instead.
        core.set_staff_venue(STAFF, self.desert, "m@v.ae")
        self.assertEqual({t["subject"] for t in core.get_staff_support_tickets(STAFF)}, {"Desert question", "General"})
        self.assertTrue(core.staff_resolve_support_ticket(tickets["Desert question"], STAFF))

    def test_support_ticket_for_a_deleted_event_stays_with_its_venue(self):
        core.create_support_ticket("guest@email.com", "Refund?", "A message that is long enough", "Desert dinner tonight")
        event_id = [e for e in ev.get_all_events() if e["title"] == "Desert dinner tonight"][0]["id"]
        ev.delete_event(event_id)
        self.register_staff(venue_id=self.desert)
        self.assertEqual([t["subject"] for t in core.get_staff_support_tickets("new.staff@email.com")], ["Refund?"])
        self.assertEqual(core.get_staff_support_tickets(STAFF), [])

    def test_old_database_staff_get_a_venue_and_manager(self):
        old_path = os.path.join(self.tmp.name, "old.db")
        conn = sqlite3.connect(old_path)
        conn.execute("CREATE TABLE users (email TEXT UNIQUE, password TEXT, role TEXT NOT NULL DEFAULT 'Customer', phone TEXT)")
        conn.execute("INSERT INTO users (email, password, role) VALUES ('staff@email.com', 'pw', 'Staff')")
        conn.execute("INSERT INTO users (email, password, role) VALUES ('older.staff@email.com', 'pw', 'Staff')")
        conn.commit()
        conn.close()
        core.DB_PATH = old_path
        core.init_db()
        core.init_db()
        self.assertEqual(core.get_staff_venue(STAFF)["name"], "Burj Khalifa")
        other = core.get_staff_venue("older.staff@email.com")
        self.assertEqual(other["id"], 1)
        self.assertTrue(other["manager_email"].startswith("manager."))


if __name__ == "__main__":
    unittest.main()
