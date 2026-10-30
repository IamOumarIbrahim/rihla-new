import datetime
import os
import sys
import tempfile
import tkinter as tk
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import database as d
from payment import verify_demo_payment, DEMO_PAYMENT_DETAILS
from capacity_bar import CapacityBar


def next_weekday(names):
    day = datetime.date.today()
    while day.strftime("%A") not in names:
        day += datetime.timedelta(days=1)
    return day


class PartnerAndPaymentTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.tmp = tempfile.TemporaryDirectory()
        d.DB_PATH = os.path.join(self.tmp.name, "test_partner.db")
        d.init_db()
        self.events = {e["title"]: e for e in d.get_all_events()}
        self.safari = self.events["Red Dune Sunset Safari and Royal BBQ Dinner"]
        self.dinner = self.events["New year dinner"]
        self.safari_day = next_weekday(("Tuesday", "Thursday"))
        self.dinner_day = datetime.date(2026, 12, 31)

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass
        self.tmp.cleanup()

    # --- Capacity Bar Tests ---
    def test_capacity_bar_ratio_and_text(self):
        # Full capacity
        bar = CapacityBar(self.root, remaining=20, total=20)
        self.assertEqual(bar.remaining, 20)
        self.assertEqual(bar.total, 20)
        self.assertEqual(bar.label.cget("text"), "20 remaining")

        # More than 5 remaining
        bar.set_capacity(12, 20)
        self.assertEqual(bar.label.cget("text"), "12 remaining")

        # 5 or less remaining -> Hurry up!
        bar.set_capacity(5, 20)
        self.assertIn("Hurry up!", bar.label.cget("text"))
        self.assertIn("5 remaining", bar.label.cget("text"))

        bar.set_capacity(1, 20)
        self.assertIn("Hurry up!", bar.label.cget("text"))
        self.assertIn("1 remaining", bar.label.cget("text"))

        # 0 remaining -> Fully booked
        bar.set_capacity(0, 20)
        self.assertIn("0 remaining", bar.label.cget("text"))
        self.assertIn("Fully booked", bar.label.cget("text"))

    # --- Extended Capacity Tests ---
    def test_partner_can_book_extended_capacity_beyond_ten(self):
        # Customer booking 15 guests should fail (capped at 10)
        cust_res = d.create_booking("customer@email.com", self.safari["id"], self.safari_day.isoformat(), 15, is_partner=False)
        self.assertFalse(cust_res["success"])
        self.assertIn(f"1 to {d.MAX_GUESTS_PER_BOOKING} guests", cust_res["message"])

        # Partner booking 15 guests should succeed (extended capacity, safari capacity is 30)
        partner_res = d.create_booking(
            "partner@email.com", self.safari["id"], self.safari_day.isoformat(), 15,
            is_partner=True, client_name="VIP Tour Group"
        )
        self.assertTrue(partner_res["success"])
        self.assertEqual(partner_res["booking"]["guests"], 15)
        self.assertEqual(partner_res["booking"]["client_name"], "VIP Tour Group")

    def test_partner_can_book_multiple_times_same_day(self):
        # Both customer and partner can book multiple times on the same day if they wish
        c1 = d.create_booking("c1@email.com", self.safari["id"], self.safari_day.isoformat(), 2, is_partner=False)
        self.assertTrue(c1["success"])
        c2 = d.create_booking("c1@email.com", self.safari["id"], self.safari_day.isoformat(), 3, is_partner=False)
        self.assertTrue(c2["success"])

        # Partner CAN book multiple events for different customer groups on the same day
        p1 = d.create_booking("partner@email.com", self.safari["id"], self.safari_day.isoformat(), 4,
                              is_partner=True, client_name="Smith Family")
        self.assertTrue(p1["success"])

        p2 = d.create_booking("partner@email.com", self.safari["id"], self.safari_day.isoformat(), 6,
                              is_partner=True, client_name="Johnson Group")
        self.assertTrue(p2["success"])

        bookings = d.get_bookings_by_customer("partner@email.com")
        self.assertEqual(len(bookings), 2)
        client_names = [b["client_name"] for b in bookings]
        self.assertIn("Smith Family", client_names)
        self.assertIn("Johnson Group", client_names)

    # --- Shopping List (Cart) and Singular Payment Tests ---
    def test_partner_shopping_list_and_checkout(self):
        partner = "partner@email.com"

        # Add two events to cart
        res1 = d.add_to_cart(partner, self.safari["id"], self.safari_day.isoformat(), 8, "Smith Party")
        self.assertTrue(res1["success"])

        res2 = d.add_to_cart(partner, self.dinner["id"], self.dinner_day.isoformat(), 12, "Corporate Gala")
        self.assertTrue(res2["success"])

        self.assertEqual(d.get_cart_count(partner), 2)
        items = d.get_cart_items(partner)
        self.assertEqual(len(items), 2)
        self.assertEqual(sum(it["guests"] for it in items), 20)

        # Checkout the entire cart in a singular payment action
        checkout_res = d.checkout_cart(partner)
        self.assertTrue(checkout_res["success"])
        self.assertEqual(len(checkout_res["bookings"]), 2)

        # Cart should now be empty
        self.assertEqual(d.get_cart_count(partner), 0)

        # Partner bookings should have both bookings
        partner_bookings = d.get_bookings_by_customer(partner)
        self.assertEqual(len(partner_bookings), 2)

    def test_remove_from_cart(self):
        partner = "partner@email.com"
        d.add_to_cart(partner, self.safari["id"], self.safari_day.isoformat(), 2, "Test")
        items = d.get_cart_items(partner)
        self.assertEqual(len(items), 1)

        d.remove_from_cart(items[0]["id"], partner)
        self.assertEqual(d.get_cart_count(partner), 0)

    # --- Demo Payment Verification Tests ---
    def test_demo_payment_verification_success(self):
        # Valid Visa
        visa_data = {
            "card_type": "visa",
            "card_number": DEMO_PAYMENT_DETAILS["visa"]["card_number"],
            "cardholder": DEMO_PAYMENT_DETAILS["visa"]["cardholder"],
            "expiry": DEMO_PAYMENT_DETAILS["visa"]["expiry"],
            "cvv": DEMO_PAYMENT_DETAILS["visa"]["cvv"],
        }
        ok, msg = verify_demo_payment("visa", visa_data)
        self.assertTrue(ok)

        # Valid Mastercard
        mc_data = {
            "card_type": "mastercard",
            "card_number": DEMO_PAYMENT_DETAILS["mastercard"]["card_number"],
            "cardholder": DEMO_PAYMENT_DETAILS["mastercard"]["cardholder"],
            "expiry": DEMO_PAYMENT_DETAILS["mastercard"]["expiry"],
            "cvv": DEMO_PAYMENT_DETAILS["mastercard"]["cvv"],
        }
        ok, msg = verify_demo_payment("mastercard", mc_data)
        self.assertTrue(ok)

        # Valid Bank Transfer
        bank_data = {
            "bank_name": DEMO_PAYMENT_DETAILS["bank"]["bank_name"],
            "account_name": DEMO_PAYMENT_DETAILS["bank"]["account_name"],
            "iban": DEMO_PAYMENT_DETAILS["bank"]["iban"],
            "swift": DEMO_PAYMENT_DETAILS["bank"]["swift"],
        }
        ok, msg = verify_demo_payment("bank", bank_data)
        self.assertTrue(ok)

    def test_demo_payment_verification_failure_when_edited(self):
        # Alter card number
        bad_card = {
            "card_type": "visa",
            "card_number": "4532 0123 4567 9999", # Altered
            "cardholder": DEMO_PAYMENT_DETAILS["visa"]["cardholder"],
            "expiry": DEMO_PAYMENT_DETAILS["visa"]["expiry"],
            "cvv": DEMO_PAYMENT_DETAILS["visa"]["cvv"],
        }
        ok, msg = verify_demo_payment("visa", bad_card)
        self.assertFalse(ok)
        self.assertIn("Card number does not match", msg)

        # Alter CVV
        bad_cvv = {
            "card_type": "visa",
            "card_number": DEMO_PAYMENT_DETAILS["visa"]["card_number"],
            "cardholder": DEMO_PAYMENT_DETAILS["visa"]["cardholder"],
            "expiry": DEMO_PAYMENT_DETAILS["visa"]["expiry"],
            "cvv": "999", # Altered
        }
        ok, msg = verify_demo_payment("visa", bad_cvv)
        self.assertFalse(ok)
        self.assertIn("CVV security code does not match", msg)

        # Alter Expiry
        bad_exp = {
            "card_type": "visa",
            "card_number": DEMO_PAYMENT_DETAILS["visa"]["card_number"],
            "cardholder": DEMO_PAYMENT_DETAILS["visa"]["cardholder"],
            "expiry": "01/25", # Altered
            "cvv": DEMO_PAYMENT_DETAILS["visa"]["cvv"],
        }
        ok, msg = verify_demo_payment("visa", bad_exp)
        self.assertFalse(ok)
        self.assertIn("Expiry date does not match", msg)

        # Alter Bank IBAN
        bad_iban = {
            "bank_name": DEMO_PAYMENT_DETAILS["bank"]["bank_name"],
            "account_name": DEMO_PAYMENT_DETAILS["bank"]["account_name"],
            "iban": "AE000000000000000000000", # Altered
            "swift": DEMO_PAYMENT_DETAILS["bank"]["swift"],
        }
        ok, msg = verify_demo_payment("bank", bad_iban)
        self.assertFalse(ok)
        self.assertIn("IBAN does not match", msg)


if __name__ == "__main__":
    unittest.main()
