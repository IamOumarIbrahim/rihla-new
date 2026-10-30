import tkinter as tk
from tkinter import messagebox, ttk
from collections import Counter
from datetime import datetime
import theme as t
from config import ADMIN_ROLE
from database import get_all_users, set_user_banned, get_reports, resolve_report
from .users_welcome import BaseWelcomeScreen
from .table_style import (GEAR, CHECKED, UNCHECKED, TABLE_STYLE, style_tables, heading_text, stripe_tags,
                          build_count_table)

LOCKED = "–"  # checkbox cell of a row that cannot be selected (an admin account)

# Columns of the users table: (key, heading, width, anchor, filterable)
USER_COLUMNS = [
    ("select", CHECKED, 50, "center", False),
    ("email", "Email", 260, "w", False),
    ("role", "Account Type", 140, "center", True),
    ("created", "Signed Up", 170, "center", False),
    ("age", "Account Age", 150, "center", False),
    ("status", "Status", 110, "center", True),
]


def parse_timestamp(text):
    try:
        return datetime.strptime((text or "")[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def account_age(created_at, now=None):
    """How long ago the account was made, in words: 'Today', '5 days', '3 months', '1 year, 2 months'."""
    created = parse_timestamp(created_at)
    if created is None:
        return "Unknown"
    days = max(((now or datetime.now()) - created).days, 0)
    if days == 0:
        return "Today"
    if days < 31:
        return f"{days} day{'s' if days != 1 else ''}"
    months = days * 12 // 365
    if months < 12:
        return f"{months} month{'s' if months != 1 else ''}"
    years, months = divmod(months, 12)
    text = f"{years} year{'s' if years != 1 else ''}"
    return f"{text}, {months} month{'s' if months != 1 else ''}" if months else text


def format_signup(created_at):
    created = parse_timestamp(created_at)
    return created.strftime("%d %b %Y, %H:%M") if created else (created_at or "Unknown")


class AdminWelcomeScreen(BaseWelcomeScreen):
    def __init__(self, root, email):
        super().__init__(root, email, ADMIN_ROLE)
        self.root = root
        self.email = email

        self.selected = set()  # emails
        self.hidden = {}  # column key -> values hidden by its filter

        self.report_filter = "Open"

        self.add_nav_button("User Accounts", self.build_users_content, icon="users")
        self.add_nav_button("Reports", self.build_reports_content, icon="alert")
        self.build_users_content()

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _is_protected(self, user):
        """Admins (including yourself) cannot be banned, so their rows cannot be selected."""
        return user["role"] == ADMIN_ROLE or user["email"].lower() == self.email.lower()

    @staticmethod
    def _get_val_for_col(user, col_key):
        if col_key == "email":
            return user["email"]
        if col_key == "role":
            return user["role"]
        if col_key == "created":
            return format_signup(user["created_at"])
        if col_key == "age":
            return account_age(user["created_at"])
        if col_key == "status":
            return "Banned" if user["banned"] else "Active"
        return ""

    def _passes_filters(self, user):
        return all(str(self._get_val_for_col(user, ck)) not in vals for ck, vals in self.hidden.items())

    # ------------------------------------------------------------------
    # page
    # ------------------------------------------------------------------
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
            messagebox.showerror("Error", f"Could not load the user list: {e}")
            return

        banned_count = sum(1 for u in users if u["banned"])
        stats = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        stats.pack(fill=tk.X, padx=30, pady=(0, 10))
        for label, value in [("Total accounts", len(users)), ("Active", len(users) - banned_count), ("Banned", banned_count)]:
            box = tk.Frame(stats, bg=t.CARD_BG, padx=14, pady=8, highlightthickness=1, highlightbackground=t.BORDER)
            box.pack(side=tk.LEFT, padx=(0, 10))
            tk.Label(box, text=label, font=(t.FONT, 8, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w")
            tk.Label(box, text=str(value), font=(t.FONT, 13, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w")

        build_count_table(self.scrollable_frame, [u["role"] for u in users], label="Account Type").pack(anchor="w", padx=30, pady=(0, 12))

        by_email = {u["email"]: u for u in users}
        self.selected &= {e for e, u in by_email.items() if not self._is_protected(u)}
        visible = [u for u in users if self._passes_filters(u)]

        tk.Label(self.scrollable_frame, text=f"Click a row to select it. Click a heading with {GEAR} to filter that column, or {CHECKED} to select all. "
                                             "Admin accounts cannot be selected.",
                 font=(t.FONT, 9), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 4))

        frame = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
        frame.pack(fill=tk.X, padx=30, pady=2)
        col_keys = [c[0] for c in USER_COLUMNS]
        tree = ttk.Treeview(frame, columns=col_keys, show="headings", height=min(max(len(visible), 3), 12),
                            style=TABLE_STYLE, selectmode="none")
        stripe_tags(tree)
        tree.tag_configure("banned", foreground="#c0392b")

        selectable = [u["email"] for u in visible if not self._is_protected(u)]

        def toggle_all():
            if selectable and all(e in self.selected for e in selectable):
                self.selected.difference_update(selectable)
            else:
                self.selected.update(selectable)
            refresh_rows()

        for col_key, heading, width, anchor, filterable in USER_COLUMNS:
            if col_key == "select":
                tree.heading(col_key, text=heading, command=toggle_all)
            elif filterable:
                tree.heading(col_key, text=heading_text(heading, bool(self.hidden.get(col_key))), anchor=anchor,
                             command=lambda ck=col_key, h=heading: self._open_filter_window(ck, h, users))
            else:
                tree.heading(col_key, text=heading, anchor=anchor)
            tree.column(col_key, width=width, minwidth=width, anchor=anchor, stretch=col_key == "email")

        for u in visible:
            tree.insert("", tk.END, iid=u["email"], values=[""] + [self._get_val_for_col(u, ck) for ck in col_keys[1:]])

        def refresh_rows():
            for i, email in enumerate(tree.get_children()):
                user = by_email[email]
                picked = email in self.selected
                vals = list(tree.item(email, "values"))
                vals[0] = LOCKED if self._is_protected(user) else (CHECKED if picked else UNCHECKED)
                tags = ["picked" if picked else ("odd" if i % 2 else "even")]
                if user["banned"]:
                    tags.append("banned")
                tree.item(email, values=vals, tags=tags)
            refresh_buttons()

        def on_click(event):
            if tree.identify("region", event.x, event.y) != "cell":
                return
            email = tree.identify_row(event.y)
            if not email or self._is_protected(by_email[email]):
                return
            self.selected.symmetric_difference_update({email})
            refresh_rows()

        tree.bind("<Button-1>", on_click)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        if not visible:
            tk.Label(self.scrollable_frame, text=f"All rows are hidden by your column filters. Click a {GEAR} heading to change them.",
                     font=(t.FONT, 9, "italic"), bg=t.PAGE_BG, fg="#e74c3c").pack(anchor="w", padx=30)

        btn_frame = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        btn_frame.pack(fill=tk.X, padx=30, pady=(10, 20))
        ban_btn = tk.Button(btn_frame, font=(t.FONT, 10, "bold"), fg="white", relief="flat", cursor="hand2",
                            command=lambda: self._change_ban(by_email, True))
        ban_btn.pack(side=tk.LEFT, ipadx=12, ipady=6)
        restore_btn = tk.Button(btn_frame, font=(t.FONT, 10, "bold"), fg="white", relief="flat", cursor="hand2",
                                command=lambda: self._change_ban(by_email, False))
        restore_btn.pack(side=tk.LEFT, padx=10, ipadx=12, ipady=6)

        def refresh_buttons():
            to_ban = [e for e in self.selected if not by_email[e]["banned"]]
            to_restore = [e for e in self.selected if by_email[e]["banned"]]
            ban_btn.config(text=f"Ban Selected ({len(to_ban)})", state=tk.NORMAL if to_ban else tk.DISABLED,
                           bg="#e74c3c" if to_ban else "#bdc3c7")
            restore_btn.config(text=f"Restore Selected ({len(to_restore)})", state=tk.NORMAL if to_restore else tk.DISABLED,
                               bg="#27ae60" if to_restore else "#bdc3c7")

        refresh_rows()

    def _change_ban(self, by_email, banned):
        emails = sorted(e for e in self.selected if by_email[e]["banned"] != banned)
        if not emails:
            return
        listed = "\n".join(emails[:10]) + (f"\n...and {len(emails) - 10} more" if len(emails) > 10 else "")
        if banned:
            question = f"Ban {len(emails)} account(s)? They will no longer be able to sign in.\n\n{listed}"
        else:
            question = f"Restore {len(emails)} account(s)? They will be able to sign in again.\n\n{listed}"
        if not messagebox.askyesno("Ban accounts" if banned else "Restore accounts", question, icon="warning" if banned else "question"):
            return

        failures = []
        for email in emails:
            result = set_user_banned(self.email, email, banned)
            if not result.get("success"):
                failures.append(f"{email}: {result.get('message', 'failed')}")
        self.selected.difference_update(emails)
        if failures:
            messagebox.showwarning("Some accounts were not changed", "\n".join(failures))
        else:
            messagebox.showinfo("Done", f"{len(emails)} account(s) {'banned' if banned else 'restored'}.")
        self.build_users_content()

    def _open_filter_window(self, col_key, col_name, users):
        popup = tk.Toplevel(self.root)
        popup.title(f"Filter: {col_name}")
        popup.configure(bg=t.CARD_BG)
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()

        tk.Label(popup, text=f"{GEAR} Filter {col_name}", font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=15, pady=(15, 10))

        counts = Counter(str(self._get_val_for_col(u, col_key)) for u in users)
        hidden = self.hidden.get(col_key, set())
        var_dict = {}
        frame_chk = tk.Frame(popup, bg=t.CARD_BG)
        frame_chk.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        for val in sorted(counts, key=str.lower):
            var = tk.BooleanVar(value=(val not in hidden))
            var_dict[val] = var
            tk.Checkbutton(frame_chk, text=f"{val}  ({counts[val]})", variable=var, bg=t.CARD_BG, font=(t.FONT, 9),
                           fg=t.TEXT, activebackground=t.CARD_BG, anchor="w").pack(fill=tk.X, pady=1)

        def apply_filter():
            self.hidden[col_key] = {val for val, var in var_dict.items() if not var.get()}
            popup.destroy()
            self.build_users_content()

        def clear_filter():
            self.hidden.pop(col_key, None)
            popup.destroy()
            self.build_users_content()

        btns = tk.Frame(popup, bg=t.CARD_BG)
        btns.pack(fill=tk.X, padx=15, pady=15)
        tk.Button(btns, text="Apply Filter", font=(t.FONT, 9, "bold"), bg=t.PRIMARY, fg="white", relief="flat",
                  cursor="hand2", command=apply_filter).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        tk.Button(btns, text="Clear", font=(t.FONT, 9), bg=t.CHIP_BG, fg=t.TEXT, relief="flat",
                  cursor="hand2", command=clear_filter).pack(side=tk.LEFT, padx=(8, 0), ipady=5, ipadx=10)
        popup.bind("<Escape>", lambda e: popup.destroy())


    # ------------------------------------------------------------------
    # reports inbox
    # ------------------------------------------------------------------
    def build_reports_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        tk.Label(self.scrollable_frame, text="Reports", font=(t.FONT, 22, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 5))
        tk.Label(self.scrollable_frame, text="Reports sent in by customers, vendors, staff, partners and dispatchers. Oldest open report first.",
                 font=(t.FONT, 11), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 12))

        try:
            reports = get_reports(self.email)
        except Exception as e:
            messagebox.showerror("Error", f"Could not load reports: {e}")
            return

        def show_tab(name):
            self.report_filter = name
            self.build_reports_content()

        open_count = sum(1 for r in reports if r["status"] == "Open")
        tabs = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        tabs.pack(fill=tk.X, padx=30, pady=(0, 10))
        for name, count in [("Open", open_count), ("Resolved", len(reports) - open_count), ("All", len(reports))]:
            active = self.report_filter == name
            tk.Button(tabs, text=f"{name} ({count})", font=(t.FONT, 9, "bold" if active else "normal"),
                      bg=t.PRIMARY if active else t.CHIP_BG, fg="white" if active else t.TEXT, relief="flat", cursor="hand2",
                      command=lambda n=name: show_tab(n)).pack(side=tk.LEFT, padx=(0, 6), ipadx=10, ipady=3)

        shown = [r for r in reports if self.report_filter == "All" or r["status"] == self.report_filter]
        if not shown:
            tk.Label(self.scrollable_frame, text="No reports here.", font=(t.FONT, 10, "italic"), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=8)
            return
        for report in shown:
            self._build_report_row(report)

    def _build_report_row(self, report):
        is_open = report["status"] == "Open"
        # Coloured strip on the left: orange while open, green once resolved
        outer = tk.Frame(self.scrollable_frame, bg=t.ACCENT if is_open else "#27ae60")
        outer.pack(fill=tk.X, padx=30, pady=4)
        box = tk.Frame(outer, bg=t.CARD_BG, highlightthickness=1, highlightbackground=t.BORDER)
        box.pack(fill=tk.X, padx=(4, 0))

        actions = tk.Frame(box, bg=t.CARD_BG)
        actions.pack(side=tk.RIGHT, padx=12, pady=10)
        body = tk.Frame(box, bg=t.CARD_BG)
        body.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=12, pady=8)

        head = tk.Frame(body, bg=t.CARD_BG)
        head.pack(fill=tk.X)
        tk.Label(head, text=f"#{report['id']}  {report['subject']}", font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(side=tk.LEFT)
        tk.Label(head, text=format_signup(report["created_at"]), font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.RIGHT)

        about = report["offender_type"] + (f": {report['offender_email']}" if report["offender_email"] else "")
        tk.Label(body, text=f"{report['category']}  |  From {report['reporter_email']} ({report['reporter_role']})  |  About {about}",
                 font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED, anchor="w", justify="left", wraplength=620).pack(fill=tk.X, pady=(2, 4))
        tk.Label(body, text=report["description"], font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT, anchor="w",
                 justify="left", wraplength=620).pack(fill=tk.X)

        if is_open:
            resolve_btn = tk.Button(actions, text="Resolve", width=14, font=(t.FONT, 9, "bold"), bg="#27ae60", fg="white",
                                    relief="flat", cursor="hand2", command=lambda: self._resolve(report))
            resolve_btn.pack(pady=(0, 6), ipady=4)
            t.add_hover(resolve_btn, "#27ae60", "#229954")
            ban_btn = tk.Button(actions, text="Ban offender", width=14, font=(t.FONT, 9, "bold"), bg="#e74c3c", fg="white",
                                relief="flat", cursor="hand2", command=lambda: self._open_ban_picker(report))
            ban_btn.pack(ipady=4)
            t.add_hover(ban_btn, "#e74c3c", "#c0392b")
        else:
            tk.Label(body, text=f"Resolved by {report['resolved_by']} on {format_signup(report['resolved_at'])}: {report['resolution']}",
                     font=(t.FONT, 9, "italic"), bg=t.CARD_BG, fg="#27ae60", anchor="w").pack(fill=tk.X, pady=(4, 0))

    def _resolve(self, report, resolution="Resolved"):
        result = resolve_report(self.email, report["id"], resolution)
        if not result.get("success"):
            messagebox.showerror("Error", result.get("message", "Could not resolve the report."))
        self.build_reports_content()

    def _open_ban_picker(self, report):
        try:
            users = [u for u in get_all_users(self.email) if not u["banned"] and not self._is_protected(u)]
        except Exception as e:
            messagebox.showerror("Error", f"Could not load the user list: {e}")
            return

        popup = tk.Toplevel(self.root)
        popup.title("Ban offender")
        popup.configure(bg=t.CARD_BG)
        popup.geometry("480x460")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()

        tk.Label(popup, text="Ban offender", font=(t.FONT, 13, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=16, pady=(14, 0))
        about = report["offender_type"] + (f" ({report['offender_email']})" if report["offender_email"] else "")
        tk.Label(popup, text=f"Report #{report['id']} is about: {about}", font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED,
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

        shown = []

        def picked_user():
            sel = listbox.curselection()
            return shown[sel[0]] if sel and sel[0] < len(shown) else None

        def on_pick(*_):
            user = picked_user()
            chosen_var.set(f"Selected: {user['email']} ({user['role']})" if user else "No user selected")
            ban_btn.config(state=tk.NORMAL if user else tk.DISABLED, bg="#e74c3c" if user else "#bdc3c7")

        def refresh_list(*_):
            needle = search_var.get().strip().lower()
            shown[:] = [u for u in users if needle in u["email"].lower() or needle in u["role"].lower()]
            listbox.delete(0, tk.END)
            for u in shown:
                listbox.insert(tk.END, f"{u['email']}    ({u['role']}, {account_age(u['created_at'])})")
            if not shown:
                listbox.insert(tk.END, "No matching users")
            on_pick()

        def ban_user():
            user = picked_user()
            if not user:
                return
            if not messagebox.askyesno("Ban user", f"Ban {user['email']}? They will no longer be able to sign in, "
                                                   f"and report #{report['id']} will be marked resolved.",
                                       icon="warning", parent=popup):
                return
            result = set_user_banned(self.email, user["email"], True)
            if not result.get("success"):
                messagebox.showerror("Error", result.get("message", "Could not ban this user."), parent=popup)
                return
            popup.destroy()
            self._resolve(report, f"Banned {user['email']}")

        ban_btn.config(command=ban_user)
        listbox.bind("<<ListboxSelect>>", on_pick)
        listbox.bind("<Double-Button-1>", lambda e: ban_user())
        search_var.trace_add("write", refresh_list)
        popup.bind("<Escape>", lambda e: popup.destroy())
        refresh_list()

        # Start on the person named in the report, if they have an account
        named = report["offender_email"].lower()
        for i, u in enumerate(shown):
            if named and u["email"].lower() == named:
                listbox.selection_set(i)
                listbox.see(i)
                on_pick()
                break
        search_entry.focus_set()


def show_admin_welcome(root, email):
    AdminWelcomeScreen(root, email)
