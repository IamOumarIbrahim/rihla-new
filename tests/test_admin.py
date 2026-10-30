import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "server"))

import database_core as core

ADMIN = "admin@email.com"


class AdminTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        core.DB_PATH = os.path.join(self.tmp.name, "test.db")
        core.init_db()

    def tearDown(self):
        self.tmp.cleanup()

    def test_admin_demo_account_exists_and_can_sign_in(self):
        self.assertEqual(core.get_role(ADMIN), "Admin")
        self.assertTrue(core.check_login(ADMIN, "admin1234"))

    def test_sign_up_cannot_create_an_admin(self):
        self.assertTrue(core.register_user("sneaky@email.com", "password123", role="Admin"))
        self.assertEqual(core.get_role("sneaky@email.com"), "Customer")

    def test_new_users_get_a_signup_time(self):
        core.register_user("new@email.com", "password123")
        user = [u for u in core.get_all_users(ADMIN) if u["email"] == "new@email.com"][0]
        created = datetime.strptime(user["created_at"], "%Y-%m-%d %H:%M:%S")
        self.assertLess(abs((datetime.now() - created).total_seconds()), 60)
        self.assertFalse(user["banned"])

    def test_only_admins_can_list_users(self):
        self.assertIsNone(core.get_all_users("customer@email.com"))
        emails = {u["email"] for u in core.get_all_users(ADMIN)}
        self.assertIn("vendor@email.com", emails)

    def test_banned_user_cannot_sign_in_until_restored(self):
        result = core.set_user_banned(ADMIN, "customer@email.com", True)
        self.assertTrue(result["success"])
        self.assertEqual(core.login_status("customer@email.com", "customer1234"), "banned")
        self.assertFalse(core.check_login("customer@email.com", "customer1234"))
        # A wrong password still just says "invalid", so the ban is not revealed to strangers.
        self.assertEqual(core.login_status("customer@email.com", "wrong"), "invalid")
        core.set_user_banned(ADMIN, "customer@email.com", False)
        self.assertTrue(core.check_login("customer@email.com", "customer1234"))

    def test_admin_cannot_ban_self_other_admins_or_act_as_non_admin(self):
        self.assertFalse(core.set_user_banned(ADMIN, ADMIN, True)["success"])
        with core._connect() as conn:
            conn.execute("INSERT INTO users (email, password, role, created_at) VALUES ('boss@email.com', 'x', 'Admin', '2026-01-01 10:00:00')")
        self.assertFalse(core.set_user_banned(ADMIN, "boss@email.com", True)["success"])
        self.assertFalse(core.set_user_banned("vendor@email.com", "customer@email.com", True)["success"])
        self.assertFalse(core.set_user_banned(ADMIN, "nobody@email.com", True)["success"])

    def test_old_database_gets_signup_dates_and_ban_columns(self):
        old_path = os.path.join(self.tmp.name, "old.db")
        conn = sqlite3.connect(old_path)
        conn.execute("CREATE TABLE users (email TEXT UNIQUE, password TEXT, role TEXT NOT NULL DEFAULT 'Customer', phone TEXT)")
        conn.execute("INSERT INTO users (email, password, role) VALUES ('old@email.com', 'pw', 'Customer')")
        conn.execute("INSERT INTO users (email, password, role) VALUES ('quiet@email.com', 'pw', 'Customer')")
        conn.execute("CREATE TABLE support_tickets (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_email TEXT NOT NULL, "
                     "subject TEXT NOT NULL, message TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Open', "
                     "created_at TEXT DEFAULT CURRENT_TIMESTAMP, resolved_by TEXT, resolved_at TEXT)")
        conn.execute("INSERT INTO support_tickets (customer_email, subject, message, created_at) "
                     "VALUES ('old@email.com', 'Hi', 'An old question', '2025-03-04 05:06:07')")
        conn.commit()
        conn.close()
        core.DB_PATH = old_path
        core.init_db()
        core.init_db()
        users = {u["email"]: u for u in core.get_all_users(ADMIN)}
        # Backfilled from the earliest thing the account did, otherwise the upgrade time.
        self.assertEqual(users["old@email.com"]["created_at"], "2025-03-04 05:06:07")
        self.assertTrue(users["quiet@email.com"]["created_at"].startswith(datetime.now().strftime("%Y-%m-%d")))
        self.assertFalse(users["old@email.com"]["banned"])
        self.assertTrue(core.check_login("old@email.com", "pw"))


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        core.DB_PATH = os.path.join(self.tmp.name, "test.db")
        core.init_db()

    def tearDown(self):
        self.tmp.cleanup()

    def report(self, reporter="customer@email.com", **kw):
        args = dict(category="Safety concern", offender_type="Staff member", subject="Unsafe driving",
                    description="The driver was speeding on the highway.", offender_email="")
        args.update(kw)
        return core.create_report(reporter, **args)

    def test_report_reaches_admin_and_can_be_resolved(self):
        result = self.report(offender_email="staff@email.com")
        self.assertTrue(result["success"])
        reports = core.get_reports(ADMIN)
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0]["reporter_role"], "Customer")
        self.assertEqual(reports[0]["offender_email"], "staff@email.com")
        self.assertEqual(reports[0]["status"], "Open")
        self.assertTrue(core.resolve_report(ADMIN, result["report_id"], "Banned staff@email.com")["success"])
        self.assertEqual(core.get_reports(ADMIN)[0]["resolution"], "Banned staff@email.com")
        self.assertFalse(core.resolve_report(ADMIN, result["report_id"])["success"])

    def test_report_rules(self):
        self.assertFalse(self.report(category="")["success"])
        self.assertFalse(self.report(description="short")["success"])
        self.assertFalse(self.report(offender_email="customer@email.com")["success"])
        self.assertFalse(self.report(reporter=ADMIN)["success"])
        self.assertFalse(self.report(reporter="nobody@email.com")["success"])
        for _ in range(core.MAX_OPEN_REPORTS):
            self.assertTrue(self.report(reporter="vendor@email.com")["success"])
        self.assertFalse(self.report(reporter="vendor@email.com")["success"])

    def test_only_admins_read_or_resolve_reports(self):
        report_id = self.report()["report_id"]
        self.assertIsNone(core.get_reports("staff@email.com"))
        self.assertFalse(core.resolve_report("staff@email.com", report_id)["success"])


if __name__ == "__main__":
    unittest.main()
