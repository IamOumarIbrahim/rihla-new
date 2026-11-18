import datetime
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "server"))

import db_test_helpers as d
import database_core as core
import database_events as events


# Phase 3: rules from the SDS tables 26 and 27 that had no test yet.
# Each test uses equivalence classes (one value from each class)
# and boundary values (on the edge, just inside and just outside).


def next_weekday(names):
    day = datetime.date.today() + datetime.timedelta(days=3)
    while day.strftime("%A") not in names:
        day += datetime.timedelta(days=1)
    return day


class SsnRuleTests(unittest.TestCase):
    def test_customer_needs_no_ssn(self):
        self.assertIsNone(core.ssn_error("Customer", ""))

    def test_valid_ssn_is_accepted(self):
        self.assertIsNone(core.ssn_error("Vendor", "4000100020003001"))

    def test_spaces_and_dashes_are_ignored(self):
        self.assertIsNone(core.ssn_error("Partner", "4000-1000-2000-3001"))
        self.assertIsNone(core.ssn_error("Partner", "4000 1000 2000 3001"))

    def test_missing_ssn_is_refused(self):
        self.assertIn("required", core.ssn_error("Staff", ""))

    def test_length_boundaries(self):
        self.assertIsNotNone(core.ssn_error("Vendor", "400010002000300"))    # 15 digits
        self.assertIsNone(core.ssn_error("Vendor", "4000100020003001"))      # 16 digits
        self.assertIsNotNone(core.ssn_error("Vendor", "40001000200030011"))  # 17 digits

    def test_letters_are_refused(self):
        self.assertIsNotNone(core.ssn_error("Dispatcher", "40001000200030AB"))

    def test_one_repeated_digit_is_refused(self):
        self.assertIn("real SSN", core.ssn_error("Vendor", "1111111111111111"))


class PasswordRuleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d.use_test_schema()
        core.init_db()

    def tearDown(self):
        self.tmp.cleanup()

    def test_sign_up_password_boundaries(self):
        self.assertFalse(core.register_user("seven@email.com", "abc1234"))    # 7 characters
        self.assertTrue(core.register_user("eight@email.com", "abcd1234"))    # 8 characters

    def test_password_change_needs_eight_characters(self):
        self.assertFalse(core.update_password("customer@email.com", "abc123"))
        self.assertTrue(core.check_login("customer@email.com", "customer1234"))
        self.assertTrue(core.update_password("customer@email.com", "newpass12"))
        self.assertTrue(core.check_login("customer@email.com", "newpass12"))

    def test_api_refuses_a_short_password(self):
        import server
        client = server.app.test_client()
        reply = client.post("/api/users/register", json={"email": "short@email.com", "password": "abc"})
        self.assertEqual(reply.status_code, 400)
        reply = client.put("/api/users/password", json={"email": "customer@email.com", "new_password": "abc"})
        self.assertEqual(reply.status_code, 400)


class BookingLimitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d.use_test_schema()
        d.init_db()
        all_events = {e["title"]: e for e in d.get_all_events()}
        self.safari = all_events["Red Dune Sunset Safari and Royal BBQ Dinner"]
        self.day = next_weekday(("Tuesday", "Thursday")).isoformat()

    def tearDown(self):
        self.tmp.cleanup()

    def test_guest_boundaries_for_a_customer(self):
        results = []
        for guests in (0, 1, 10, 11):
            r = d.create_booking("guest@email.com", self.safari["id"], self.day, guests)
            results.append(r["success"])
        self.assertEqual(results, [False, True, True, False])

    def test_capacity_boundaries(self):
        for good in (1, 5000):
            d.create_event("Edge " + str(good), "General", "10 AED", "a long enough description",
                           "vendor@email.com", 1, "2030-01-01 10:00", "One-Time", "N/A", "10:00", capacity=good)
        titles = [e["title"] for e in d.get_all_events()]
        self.assertIn("Edge 1", titles)
        self.assertIn("Edge 5000", titles)

    def test_cancel_reason_boundaries(self):
        booking = d.create_booking("guest@email.com", self.safari["id"], self.day, 1)["booking"]
        vendor = self.safari["vendor_email"]
        self.assertFalse(d.vendor_cancel_booking(booking["id"], vendor, "")["success"])
        self.assertFalse(d.vendor_cancel_booking(booking["id"], vendor, "x" * 301)["success"])
        self.assertTrue(d.vendor_cancel_booking(booking["id"], vendor, "x" * 300)["success"])


class PriceAndCodeTests(unittest.TestCase):
    def test_vat_is_five_percent(self):
        self.assertEqual(events.add_vat(720), (720, 36, 756))
        self.assertEqual(events.add_vat(0), (0, 0, 0))

    def test_price_text_to_number(self):
        self.assertEqual(d.price_to_int("240 AED"), 240)
        self.assertEqual(d.price_to_int(""), 0)

    def test_ticket_code_is_shown_in_groups_of_four(self):
        self.assertEqual(d.format_ticket_code("1234567890123456"), "1234 5678 9012 3456")


class RatingRuleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d.use_test_schema()
        d.init_db()

    def tearDown(self):
        self.tmp.cleanup()

    def test_rating_classes(self):
        for bad in (4.3, 5.5, -1, "abc"):
            result = events.submit_review("customer@email.com", 1, bad)
            self.assertFalse(result["success"])
            self.assertIn("rating", result["message"])

    def test_good_ratings_pass_the_rating_check(self):
        # booking 999 does not exist, so it fails later, but not because of the rating
        for good in (0, 3.5, 5):
            result = events.submit_review("customer@email.com", 999, good)
            self.assertNotIn("steps of 0.5", result.get("message", ""))


if __name__ == "__main__":
    unittest.main()
