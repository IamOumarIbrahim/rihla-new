import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
import theme as t
from config import ADMIN_ROLE
from database import get_all_users, set_user_banned, get_reports, resolve_report, get_all_bookings, admin_cancel_booking
from .users_welcome import BaseWelcomeScreen
from .cancellation import page_header, cancelled_line, ask_reason, cancel_button
from .table_style import (GEAR, CHECKED, UNCHECKED, TABLE_STYLE, style_tables, heading_text, stripe_tags,
                          build_count_table)

LOCKED = "–"  # checkbox cell for a row you cant select (admin account)

# columns of the users table: (key, heading, width, anchor, can filter)
USER_COLUMNS = [
    ("select", CHECKED, 50, "center", False),
    ("email", "Email", 260, "w", False),
    ("role", "Account Type", 140, "center", True),
    ("created", "Signed Up", 150, "center", False),
    ("age", "Account Age", 110, "center", False),
    ("status", "Status", 100, "center", True),
    # only for staff: their venue and its manager (empty for the others)
    ("venue", "Venue", 180, "w", True),
    ("manager", "Manager Email", 220, "w", False),
]


def parse_timestamp(text):
    if not text:
        text = ""
    try:
        return datetime.strptime(text[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


# how old the account is in words: 'Today', '5 days', '3 months', '1 year, 2 months'
def account_age(created_at, now=None):
    created = parse_timestamp(created_at)
    if created is None:
        return "Unknown"
    if now is None:
        now = datetime.now()
    days = (now - created).days
    if days < 0:
        days = 0
    if days == 0:
        return "Today"
    if days < 31:
        if days != 1:
            return str(days) + " days"
        return str(days) + " day"

    # months = days * 12 / 365
    months = days * 12 // 365
    if months < 12:
        if months != 1:
            return str(months) + " months"
        return str(months) + " month"
    years = months // 12
    months = months % 12
    if years != 1:
        text = str(years) + " years"
    else:
        text = str(years) + " year"
    if months:
        if months != 1:
            return text + ", " + str(months) + " months"
        return text + ", " + str(months) + " month"
    return text


def format_signup(created_at):
    created = parse_timestamp(created_at)
    if created:
        return created.strftime("%d %b %Y, %H:%M")
    if created_at:
        return created_at
    return "Unknown"


class AdminWelcomeScreen(BaseWelcomeScreen):
    def __init__(self, root, email):
        BaseWelcomeScreen.__init__(self, root, email, ADMIN_ROLE)
        self.root = root
        self.email = email

        self.selected = set()  # emails
        self.hidden = {}  # column key -> values hidden by the filter

        self.report_filter = "Open"

        self.add_nav_button("User Accounts", self.build_users_content, icon="users")
        self.add_nav_button("Reports", self.build_reports_content, icon="alert")
        self.add_nav_button("Bookings", self.build_bookings_content, icon="ticket")
        self.build_users_content()

    # admins (and yourself) cant be banned so you cant select their rows
    def _is_protected(self, user):
        return user["role"] == ADMIN_ROLE or user["email"].lower() == self.email.lower()

    def _get_val_for_col(self, user, col_key):
        if col_key == "email":
            return user["email"]
        if col_key == "role":
            return user["role"]
        if col_key == "created":
            return format_signup(user["created_at"])
        if col_key == "age":
            return account_age(user["created_at"])
        if col_key == "status":
            if user["banned"]:
                return "Banned"
            return "Active"
        if col_key == "venue":
            return user.get("venue_name", "")
        if col_key == "manager":
            return user.get("manager_email", "")
        return ""

    def _passes_filters(self, user):
        for ck in self.hidden:
            if str(self._get_val_for_col(user, ck)) in self.hidden[ck]:
                return False
        return True

    # ====== User accounts page ======
    def build_users_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        style_tables()

        tk.Label(self.scrollable_frame, text="User Accounts", font=(t.FONT, 22, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 5))
        tk.Label(self.scrollable_frame, text="Everyone registered on Rihla. Banned accounts can no longer sign in.",
                 font=(t.FONT, 11), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 15))

        try:
            users = get_all_users(self.email)
        except Exception as e:
            messagebox.showerror("Error", "Could not load the user list: " + str(e))
            return

        banned_count = 0
        for u in users:
            if u["banned"]:
                banned_count += 1
        stats = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        stats.pack(fill=tk.X, padx=30, pady=(0, 10))
        for label, value in [("Total accounts", len(users)), ("Active", len(users) - banned_count), ("Banned", banned_count)]:
            box = tk.Frame(stats, bg=t.CARD_BG, padx=14, pady=8, highlightthickness=1, highlightbackground=t.BORDER)
            box.pack(side=tk.LEFT, padx=(0, 10))
            tk.Label(box, text=label, font=(t.FONT, 8, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w")
            tk.Label(box, text=str(value), font=(t.FONT, 13, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w")

        roles = []
        for u in users:
            roles.append(u["role"])
        build_count_table(self.scrollable_frame, roles, label="Account Type").pack(anchor="w", padx=30, pady=(0, 12))

        by_email = {}
        for u in users:
            by_email[u["email"]] = u
        # forget selected rows that cant be selected anymore
        for e in list(self.selected):
            if e not in by_email or self._is_protected(by_email[e]):
                self.selected.remove(e)
        visible = []
        for u in users:
            if self._passes_filters(u):
                visible.append(u)

        tk.Label(self.scrollable_frame, text="Click a row to select it. Click a heading with " + GEAR + " to filter that column, or " + CHECKED + " to select all. "
                                             "Admin accounts cannot be selected.",
                 font=(t.FONT, 9), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 4))

        frame = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
        frame.pack(fill=tk.X, padx=30, pady=2)
        col_keys = []
        for c in USER_COLUMNS:
            col_keys.append(c[0])
        # 3 to 12 rows high
        rows_high = len(visible)
        if rows_high < 3:
            rows_high = 3
        if rows_high > 12:
            rows_high = 12
        tree = ttk.Treeview(frame, columns=col_keys, show="headings", height=rows_high,
                            style=TABLE_STYLE, selectmode="none")
        stripe_tags(tree)
        tree.tag_configure("banned", foreground="#c0392b")

        selectable = []
        for u in visible:
            if not self._is_protected(u):
                selectable.append(u["email"])

        def toggle_all():
            all_picked = True
            for e in selectable:
                if e not in self.selected:
                    all_picked = False
            if selectable and all_picked:
                for e in selectable:
                    self.selected.discard(e)
            else:
                for e in selectable:
                    self.selected.add(e)
            refresh_rows()

        for col_key, heading, width, anchor, filterable in USER_COLUMNS:
            if col_key == "select":
                tree.heading(col_key, text=heading, command=toggle_all)
            elif filterable:
                def open_filter(ck=col_key, h=heading):
                    self._open_filter_window(ck, h, users)
                tree.heading(col_key, text=heading_text(heading, bool(self.hidden.get(col_key))), anchor=anchor,
                             command=open_filter)
            else:
                tree.heading(col_key, text=heading, anchor=anchor)
            tree.column(col_key, width=width, minwidth=width, anchor=anchor, stretch=col_key == "email")

        for u in visible:
            values = [""]
            for ck in col_keys[1:]:
                values.append(self._get_val_for_col(u, ck))
            tree.insert("", tk.END, iid=u["email"], values=values)

        def refresh_rows():
            i = 0
            for email in tree.get_children():
                user = by_email[email]
                picked = email in self.selected
                vals = list(tree.item(email, "values"))
                if self._is_protected(user):
                    vals[0] = LOCKED
                elif picked:
                    vals[0] = CHECKED
                else:
                    vals[0] = UNCHECKED
                if picked:
                    tags = ["picked"]
                elif i % 2:
                    tags = ["odd"]
                else:
                    tags = ["even"]
                if user["banned"]:
                    tags.append("banned")
                tree.item(email, values=vals, tags=tags)
                i += 1
            refresh_buttons()

        # click a row to select or unselect it
        def on_click(event):
            if tree.identify("region", event.x, event.y) != "cell":
                return
            email = tree.identify_row(event.y)
            if not email or self._is_protected(by_email[email]):
                return
            if email in self.selected:
                self.selected.remove(email)
            else:
                self.selected.add(email)
            refresh_rows()

        tree.bind("<Button-1>", on_click)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        # the Venue and Manager Email columns make the table too wide for small windows
        x_scrollbar = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=scrollbar.set, xscrollcommand=x_scrollbar.set)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        if not visible:
            tk.Label(self.scrollable_frame, text="All rows are hidden by your column filters. Click a " + GEAR + " heading to change them.",
                     font=(t.FONT, 9, "italic"), bg=t.PAGE_BG, fg="#e74c3c").pack(anchor="w", padx=30)

        def ban_clicked():
            self._change_ban(by_email, True)

        def restore_clicked():
            self._change_ban(by_email, False)

        btn_frame = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        btn_frame.pack(fill=tk.X, padx=30, pady=(10, 20))
        ban_btn = tk.Button(btn_frame, font=(t.FONT, 10, "bold"), fg="white", relief="flat", cursor="hand2",
                            command=ban_clicked)
        ban_btn.pack(side=tk.LEFT, ipadx=12, ipady=6)
        restore_btn = tk.Button(btn_frame, font=(t.FONT, 10, "bold"), fg="white", relief="flat", cursor="hand2",
                                command=restore_clicked)
        restore_btn.pack(side=tk.LEFT, padx=10, ipadx=12, ipady=6)

        def refresh_buttons():
            to_ban = 0
            to_restore = 0
            for e in self.selected:
                if by_email[e]["banned"]:
                    to_restore += 1
                else:
                    to_ban += 1
            if to_ban:
                ban_btn.config(text="Ban Selected (" + str(to_ban) + ")", state=tk.NORMAL, bg="#e74c3c")
            else:
                ban_btn.config(text="Ban Selected (0)", state=tk.DISABLED, bg="#bdc3c7")
            if to_restore:
                restore_btn.config(text="Restore Selected (" + str(to_restore) + ")", state=tk.NORMAL, bg="#27ae60")
            else:
                restore_btn.config(text="Restore Selected (0)", state=tk.DISABLED, bg="#bdc3c7")

        refresh_rows()

    def _change_ban(self, by_email, banned):
        emails = []
        for e in self.selected:
            if by_email[e]["banned"] != banned:
                emails.append(e)
        emails.sort()
        if not emails:
            return

        # show the first 10 emails in the question
        listed = "\n".join(emails[:10])
        if len(emails) > 10:
            listed = listed + "\n...and " + str(len(emails) - 10) + " more"
        if banned:
            question = "Ban " + str(len(emails)) + " account(s)? They will no longer be able to sign in.\n\n" + listed
            title = "Ban accounts"
            icon = "warning"
        else:
            question = "Restore " + str(len(emails)) + " account(s)? They will be able to sign in again.\n\n" + listed
            title = "Restore accounts"
            icon = "question"
        if not messagebox.askyesno(title, question, icon=icon):
            return

        failures = []
        for email in emails:
            result = set_user_banned(self.email, email, banned)
            if not result.get("success"):
                failures.append(email + ": " + str(result.get('message', 'failed')))
        for email in emails:
            self.selected.discard(email)
        if failures:
            messagebox.showwarning("Some accounts were not changed", "\n".join(failures))
        else:
            if banned:
                done_word = "banned"
            else:
                done_word = "restored"
            messagebox.showinfo("Done", str(len(emails)) + " account(s) " + done_word + ".")
        self.build_users_content()

    def _open_filter_window(self, col_key, col_name, users):
        popup = tk.Toplevel(self.root)
        popup.title("Filter: " + col_name)
        popup.configure(bg=t.CARD_BG)
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()

        tk.Label(popup, text=GEAR + " Filter " + col_name, font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=15, pady=(15, 10))

        # count every value
        counts = {}
        for u in users:
            val = str(self._get_val_for_col(u, col_key))
            if val in counts:
                counts[val] += 1
            else:
                counts[val] = 1
        # sort the values, not case sensitive (insertion sort)
        values = []
        for val in counts:
            values.append(val)
        for i in range(1, len(values)):
            temp = values[i]
            j = i - 1
            while j >= 0 and values[j].lower() > temp.lower():
                values[j + 1] = values[j]
                j -= 1
            values[j + 1] = temp

        hidden = self.hidden.get(col_key, set())
        var_dict = {}
        frame_chk = tk.Frame(popup, bg=t.CARD_BG)
        frame_chk.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        for val in values:
            var = tk.BooleanVar(value=(val not in hidden))
            var_dict[val] = var
            tk.Checkbutton(frame_chk, text=val + "  (" + str(counts[val]) + ")", variable=var, bg=t.CARD_BG, font=(t.FONT, 9),
                           fg=t.TEXT, activebackground=t.CARD_BG, anchor="w").pack(fill=tk.X, pady=1)

        def apply_filter():
            hidden_now = set()
            for val in var_dict:
                if not var_dict[val].get():
                    hidden_now.add(val)
            self.hidden[col_key] = hidden_now
            popup.destroy()
            self.build_users_content()

        def clear_filter():
            if col_key in self.hidden:
                del self.hidden[col_key]
            popup.destroy()
            self.build_users_content()

        def on_escape(event):
            popup.destroy()

        btns = tk.Frame(popup, bg=t.CARD_BG)
        btns.pack(fill=tk.X, padx=15, pady=15)
        tk.Button(btns, text="Apply Filter", font=(t.FONT, 9, "bold"), bg=t.PRIMARY, fg="white", relief="flat",
                  cursor="hand2", command=apply_filter).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        tk.Button(btns, text="Clear", font=(t.FONT, 9), bg=t.CHIP_BG, fg=t.TEXT, relief="flat",
                  cursor="hand2", command=clear_filter).pack(side=tk.LEFT, padx=(8, 0), ipady=5, ipadx=10)
        popup.bind("<Escape>", on_escape)


    # ====== Bookings (admin can cancel any booking, full refund) ======
    def build_bookings_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        style_tables()

        page_header(self.scrollable_frame, "Bookings", self.build_bookings_content)
        tk.Label(self.scrollable_frame, text="Every booking on Rihla. Cancelling here refunds the customer in full (VAT included) and needs a reason.",
                 font=(t.FONT, 11), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 12))

        try:
            bookings = get_all_bookings(self.email)
        except Exception as e:
            messagebox.showerror("Error", "Could not load bookings: " + str(e))
            return
        if not bookings:
            tk.Label(self.scrollable_frame, text="No bookings yet.", font=(t.FONT, 10, "italic"), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30)
            return

        columns = [("event", "Event", 220, "w"), ("date", "Date", 100, "center"), ("customer", "Booked by", 200, "w"),
                   ("guests", "Guests", 60, "center"), ("total", "Total (AED)", 100, "e"),
                   ("refund", "Refunded (AED)", 120, "e"), ("status", "Status", 100, "center")]
        frame = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
        frame.pack(fill=tk.X, padx=30, pady=2)
        keys = []
        for c in columns:
            keys.append(c[0])
        rows_high = len(bookings)
        if rows_high > 15:
            rows_high = 15
        tree = ttk.Treeview(frame, columns=keys, show="headings", height=rows_high,
                            style=TABLE_STYLE, selectmode="browse")
        stripe_tags(tree)
        tree.tag_configure("status_Cancelled", foreground="#c0392b")
        tree.tag_configure("status_Expired", foreground=t.TEXT_MUTED)
        for key, heading, width, anchor in columns:
            tree.heading(key, text=heading, anchor=anchor)
            if key == "event" or key == "customer":
                stretch = True
            else:
                stretch = False
            tree.column(key, width=width, minwidth=width, anchor=anchor, stretch=stretch)
        i = 0
        for b in bookings:
            if b.get("refund_amount") is not None:
                refund = format(b['refund_amount'], ",.2f") + " (" + str(b['refund_percent']) + "%)"
            else:
                refund = ""
            if i % 2:
                stripe = "odd"
            else:
                stripe = "even"
            tree.insert("", tk.END, iid=str(b["id"]), tags=(stripe, "status_" + str(b['status'])),
                        values=[b["event_title"], b["booking_date"], b["customer_email"], b["guests"],
                                format(float(b['total_price']), ",.2f"), refund, b["status"]])
            i += 1
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        by_id = {}
        for b in bookings:
            by_id[str(b["id"])] = b
        action_row = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        action_row.pack(fill=tk.X, padx=30, pady=(6, 10))
        cancel_btn = cancel_button(action_row)
        cancel_btn.pack(side=tk.LEFT, ipadx=10, ipady=4)
        detail = tk.Label(action_row, text="Select a booking to cancel it or see its cancellation details.",
                          font=(t.FONT, 9), bg=t.PAGE_BG, fg=t.TEXT_MUTED, wraplength=650, justify="left")
        detail.pack(side=tk.LEFT, padx=12)

        def selected_booking():
            chosen = tree.selection()
            if chosen:
                return by_id.get(chosen[0])
            return None

        def on_select(event=None):
            b = selected_booking()
            if b and b["status"] == "Confirmed":
                cancel_btn.config(state=tk.NORMAL)
            else:
                cancel_btn.config(state=tk.DISABLED)
            if not b:
                return
            if b["status"] == "Cancelled":
                detail.config(text=cancelled_line(b, self.email), fg="#c0392b")
            else:
                venue = b['venue_name']
                if not venue:
                    venue = 'Venue TBA'
                time_text = b['event_time']
                if not time_text:
                    time_text = 'TBA'
                detail.config(text="Ticket " + str(b['ticket_code']) + "  |  " + str(venue) + " at " + str(time_text),
                              fg=t.TEXT_MUTED)

        def on_cancel():
            b = selected_booking()
            if not b:
                return
            reason = ask_reason(self.root, b)
            if reason is None:
                return
            res = admin_cancel_booking(b["id"], self.email, reason)
            if res["success"]:
                messagebox.showinfo("Booking cancelled", res["message"])
            else:
                messagebox.showerror("Cannot cancel", res["message"])
            self.build_bookings_content()

        tree.bind("<<TreeviewSelect>>", on_select)
        cancel_btn.config(command=on_cancel)

    # ====== Reports inbox ======
    def build_reports_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        tk.Label(self.scrollable_frame, text="Reports", font=(t.FONT, 22, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 5))
        tk.Label(self.scrollable_frame, text="Reports sent in by customers, vendors, staff, partners and dispatchers. Oldest open report first.",
                 font=(t.FONT, 11), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 12))

        try:
            reports = get_reports(self.email)
        except Exception as e:
            messagebox.showerror("Error", "Could not load reports: " + str(e))
            return

        def show_tab(name):
            self.report_filter = name
            self.build_reports_content()

        open_count = 0
        for r in reports:
            if r["status"] == "Open":
                open_count += 1
        tabs = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        tabs.pack(fill=tk.X, padx=30, pady=(0, 10))
        for name, count in [("Open", open_count), ("Resolved", len(reports) - open_count), ("All", len(reports))]:
            if self.report_filter == name:
                weight = "bold"
                bg_col = t.PRIMARY
                fg_col = "white"
            else:
                weight = "normal"
                bg_col = t.CHIP_BG
                fg_col = t.TEXT

            def tab_clicked(n=name):
                show_tab(n)
            tk.Button(tabs, text=name + " (" + str(count) + ")", font=(t.FONT, 9, weight),
                      bg=bg_col, fg=fg_col, relief="flat", cursor="hand2",
                      command=tab_clicked).pack(side=tk.LEFT, padx=(0, 6), ipadx=10, ipady=3)

        shown = []
        for r in reports:
            if self.report_filter == "All" or r["status"] == self.report_filter:
                shown.append(r)
        if not shown:
            tk.Label(self.scrollable_frame, text="No reports here.", font=(t.FONT, 10, "italic"), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=8)
            return
        for report in shown:
            self._build_report_row(report)

    def _build_report_row(self, report):
        is_open = report["status"] == "Open"
        # color strip on the left, orange when open and green when resolved
        if is_open:
            strip = t.ACCENT
        else:
            strip = "#27ae60"
        outer = tk.Frame(self.scrollable_frame, bg=strip)
        outer.pack(fill=tk.X, padx=30, pady=4)
        box = tk.Frame(outer, bg=t.CARD_BG, highlightthickness=1, highlightbackground=t.BORDER)
        box.pack(fill=tk.X, padx=(4, 0))

        actions = tk.Frame(box, bg=t.CARD_BG)
        actions.pack(side=tk.RIGHT, padx=12, pady=10)
        body = tk.Frame(box, bg=t.CARD_BG)
        body.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=12, pady=8)

        head = tk.Frame(body, bg=t.CARD_BG)
        head.pack(fill=tk.X)
        tk.Label(head, text="#" + str(report['id']) + "  " + str(report['subject']), font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(side=tk.LEFT)
        tk.Label(head, text=format_signup(report["created_at"]), font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.RIGHT)

        about = report["offender_type"]
        if report["offender_email"]:
            about = about + ": " + report['offender_email']
        line = (str(report['category']) + "  |  From " + str(report['reporter_email']) + " (" + str(report['reporter_role'])
                + ")  |  About " + about)
        tk.Label(body, text=line,
                 font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED, anchor="w", justify="left", wraplength=620).pack(fill=tk.X, pady=(2, 4))
        tk.Label(body, text=report["description"], font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT, anchor="w",
                 justify="left", wraplength=620).pack(fill=tk.X)

        if is_open:
            def resolve_clicked():
                self._resolve(report)

            def ban_clicked():
                self._open_ban_picker(report)

            resolve_btn = tk.Button(actions, text="Resolve", width=14, font=(t.FONT, 9, "bold"), bg="#27ae60", fg="white",
                                    relief="flat", cursor="hand2", command=resolve_clicked)
            resolve_btn.pack(pady=(0, 6), ipady=4)
            t.add_hover(resolve_btn, "#27ae60", "#229954")
            ban_btn = tk.Button(actions, text="Ban offender", width=14, font=(t.FONT, 9, "bold"), bg="#e74c3c", fg="white",
                                relief="flat", cursor="hand2", command=ban_clicked)
            ban_btn.pack(ipady=4)
            t.add_hover(ban_btn, "#e74c3c", "#c0392b")
        else:
            done_text = ("Resolved by " + str(report['resolved_by']) + " on " + format_signup(report['resolved_at'])
                         + ": " + str(report['resolution']))
            tk.Label(body, text=done_text,
                     font=(t.FONT, 9, "italic"), bg=t.CARD_BG, fg="#27ae60", anchor="w").pack(fill=tk.X, pady=(4, 0))

    def _resolve(self, report, resolution="Resolved"):
        result = resolve_report(self.email, report["id"], resolution)
        if not result.get("success"):
            messagebox.showerror("Error", result.get("message", "Could not resolve the report."))
        self.build_reports_content()

    def _open_ban_picker(self, report):
        try:
            all_users = get_all_users(self.email)
        except Exception as e:
            messagebox.showerror("Error", "Could not load the user list: " + str(e))
            return
        # only users that can still be banned
        users = []
        for u in all_users:
            if not u["banned"] and not self._is_protected(u):
                users.append(u)

        popup = tk.Toplevel(self.root)
        popup.title("Ban offender")
        popup.configure(bg=t.CARD_BG)
        popup.geometry("480x460")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()

        tk.Label(popup, text="Ban offender", font=(t.FONT, 13, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=16, pady=(14, 0))
        about = report["offender_type"]
        if report["offender_email"]:
            about = about + " (" + report['offender_email'] + ")"
        tk.Label(popup, text="Report #" + str(report['id']) + " is about: " + about, font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED,
                 wraplength=440, justify="left").pack(anchor="w", padx=16, pady=(2, 10))

        tk.Label(popup, text="Search by email or account type", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=16)
        search_var = tk.StringVar()
        search_entry = tk.Entry(popup, textvariable=search_var, font=(t.FONT, 10), bg=t.FIELD_BG, relief="solid", bd=1)
        search_entry.pack(fill=tk.X, padx=16, pady=(2, 8), ipady=4)

        list_frame = tk.Frame(popup, bg=t.CARD_BG)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=16)
        listbox = tk.Listbox(list_frame, font=(t.FONT, 10), activestyle="none", selectbackground=t.PRIMARY,
                             relief="solid", bd=1, exportselection=False)
        scroll = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=scroll.set)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        chosen_var = tk.StringVar(value="No user selected")
        tk.Label(popup, textvariable=chosen_var, font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=16, pady=(8, 0))

        btns = tk.Frame(popup, bg=t.CARD_BG)
        btns.pack(fill=tk.X, padx=16, pady=12)
        ban_btn = tk.Button(btns, text="Ban user", font=(t.FONT, 10, "bold"), fg="white", relief="flat", cursor="hand2")
        ban_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        tk.Button(btns, text="Cancel", font=(t.FONT, 9), bg=t.CHIP_BG, fg=t.TEXT, relief="flat", cursor="hand2",
                  command=popup.destroy).pack(side=tk.LEFT, padx=(8, 0), ipady=5, ipadx=12)

        shown = []  # the users in the list right now

        def picked_user():
            sel = listbox.curselection()
            if sel and sel[0] < len(shown):
                return shown[sel[0]]
            return None

        def on_pick(*args):
            user = picked_user()
            if user:
                chosen_var.set("Selected: " + user['email'] + " (" + user['role'] + ")")
                ban_btn.config(state=tk.NORMAL, bg="#e74c3c")
            else:
                chosen_var.set("No user selected")
                ban_btn.config(state=tk.DISABLED, bg="#bdc3c7")

        def refresh_list(*args):
            needle = search_var.get().strip().lower()
            shown.clear()
            for u in users:
                if needle in u["email"].lower() or needle in u["role"].lower():
                    shown.append(u)
            listbox.delete(0, tk.END)
            for u in shown:
                listbox.insert(tk.END, u['email'] + "    (" + u['role'] + ", " + account_age(u['created_at']) + ")")
            if not shown:
                listbox.insert(tk.END, "No matching users")
            on_pick()

        def ban_user():
            user = picked_user()
            if not user:
                return
            question = ("Ban " + user['email'] + "? They will no longer be able to sign in, "
                        + "and report #" + str(report['id']) + " will be marked resolved.")
            if not messagebox.askyesno("Ban user", question, icon="warning", parent=popup):
                return
            result = set_user_banned(self.email, user["email"], True)
            if not result.get("success"):
                messagebox.showerror("Error", result.get("message", "Could not ban this user."), parent=popup)
                return
            popup.destroy()
            self._resolve(report, "Banned " + user['email'])

        def on_double_click(event):
            ban_user()

        def on_escape(event):
            popup.destroy()

        ban_btn.config(command=ban_user)
        listbox.bind("<<ListboxSelect>>", on_pick)
        listbox.bind("<Double-Button-1>", on_double_click)
        search_var.trace_add("write", refresh_list)
        popup.bind("<Escape>", on_escape)
        refresh_list()

        # start with the person from the report selected (if they have an account)
        named = report["offender_email"].lower()
        for i in range(len(shown)):
            if named and shown[i]["email"].lower() == named:
                listbox.selection_set(i)
                listbox.see(i)
                on_pick()
                break
        search_entry.focus_set()


def show_admin_welcome(root, email):
    AdminWelcomeScreen(root, email)
