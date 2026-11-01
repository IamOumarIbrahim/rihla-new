from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

from ui import clear_window
import navigate
from config import MIN_PASSWORD_LENGTH, ADMIN_ROLE
from database import (check_login, update_password, get_preferred_currency, set_preferred_currency,
                      get_all_venues, get_staff_venue, set_staff_venue)

STAFF_ROLE = "Staff"
from pricing import CURRENCIES, normalize_currency
from .report_view import ReportView
import theme as t
import icons as ic


# the screen every role uses: nav bar on the left, the top bar and a part on the right that scrolls
class BaseWelcomeScreen:
    def __init__(self, root, email, role_name):
        self.root = root
        self.email = email
        self.role_name = role_name
        self.username = email.split('@')[0]
        self._clock_timer = None

        clear_window(self.root)

        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.setup_nav_bar()
        self.setup_scrollable_right_area()

    def setup_nav_bar(self):
        self.nav_bar = tk.Frame(self.main_container, bg="#2c3e50", width=200)
        self.nav_bar.pack(side=tk.LEFT, fill=tk.Y)
        self.nav_bar.pack_propagate(False)

        tk.Label(self.nav_bar, text="Rihla Portal", bg="#2c3e50", fg="white", font=(t.FONT, 16, "bold")).pack(pady=(20, 5))
        tk.Label(self.nav_bar, text="[" + self.role_name + "]", bg="#2c3e50", fg="#3498db", font=(t.FONT, 10, "italic")).pack(pady=(0, 15))

        # bottom part: Settings right above Log Out for everyone
        bottom_frame = tk.Frame(self.nav_bar, bg="#2c3e50")
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 20))

        # everyone except admins can send a report, admins read them
        if self.role_name != ADMIN_ROLE:
            report_btn = tk.Button(bottom_frame, text="Report", width=20, relief="flat", bg="#34495e", fg="white",
                                   font=(t.FONT, 9, "bold"), cursor="hand2", command=self.open_report_page)
            report_btn.pack(pady=(0, 8))
            t.add_hover(report_btn, "#34495e", t.PRIMARY)

        settings_btn = tk.Button(bottom_frame, text="Settings", width=20, relief="flat", bg="#34495e", fg="white",
                                 font=(t.FONT, 9, "bold"), cursor="hand2", command=self.open_settings_modal)
        settings_btn.pack(pady=(0, 8))
        settings_img = ic.get_icon("settings", size=14, color="#ffffff", master=self.nav_bar)
        if settings_img:
            settings_btn.config(image=settings_img, compound=tk.LEFT)
            settings_btn.image = settings_img
        t.add_hover(settings_btn, "#34495e", "#2c3e50")

        logout_btn = tk.Button(bottom_frame, text="Log Out", width=20, relief="raised", bg="#e74c3c", fg="white",
                               font=(t.FONT, 9, "bold"), cursor="hand2", command=self.log_out)
        logout_btn.pack()
        logout_img = ic.get_icon("logout", size=14, color="#ffffff", master=self.nav_bar)
        if logout_img:
            logout_btn.config(image=logout_img, compound=tk.LEFT)
            logout_btn.image = logout_img
        t.add_hover(logout_btn, "#e74c3c", "#c0392b")

        # the buttons of each role go in here
        self.nav_buttons_container = tk.Frame(self.nav_bar, bg="#2c3e50")
        self.nav_buttons_container.pack(fill=tk.BOTH, expand=True)

    def log_out(self):
        navigate.show_login(self.root)

    def add_nav_button(self, text, command=None, icon=None):
        # the side nav is only text, the plus is the only icon we keep
        if icon == "plus":
            text = ic.emoji(icon) + " " + text
        btn = tk.Button(self.nav_buttons_container, text=text, width=20, relief="flat", bg="#34495e", fg="white",
                        font=(t.FONT, 9, "bold"), cursor="hand2", command=command)
        btn.pack(pady=4)
        t.add_hover(btn, "#34495e", t.PRIMARY)
        return btn

    def setup_scrollable_right_area(self):
        right_container = tk.Frame(self.main_container, bg="#ecf0f1")
        right_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # top bar with the date and time on the right
        self.top_bar = tk.Frame(right_container, bg="#ffffff", height=42, bd=0, relief="flat",
                                highlightthickness=1, highlightbackground=t.BORDER)
        self.top_bar.pack(side=tk.TOP, fill=tk.X)
        self.top_bar.pack_propagate(False)

        tk.Label(self.top_bar, text="Rihla Experience Portal  |  Signed in as " + self.email,
                 font=(t.FONT, 9), bg="#ffffff", fg=t.TEXT_MUTED).pack(side=tk.LEFT, padx=20)

        self.datetime_label = tk.Label(self.top_bar, font=(t.FONT, 10, "bold"), bg="#ffffff", fg=t.TEXT)
        self.datetime_label.pack(side=tk.RIGHT, padx=20)

        # clock and calender icons
        clock_img = ic.get_icon("clock", size=14, color=t.TEXT, master=self.top_bar)
        cal_img = ic.get_icon("calendar", size=14, color=t.TEXT, master=self.top_bar)

        # updates every second
        def update_clock():
            now = datetime.now()
            date_str = now.strftime("%a, %b %d, %Y")
            time_str = now.strftime("%I:%M:%S %p")
            self.datetime_label.config(text=ic.emoji("clock") + " | " + date_str + " " + time_str)
            self._clock_timer = self.root.after(1000, update_clock)

        update_clock()

        # the canvas that scrolls
        self.canvas = tk.Canvas(right_container, bg="#ecf0f1", highlightthickness=0)
        scrollbar = tk.Scrollbar(right_container, orient="vertical", command=self.canvas.yview)

        self.scrollable_frame = tk.Frame(self.canvas, bg="#ecf0f1")
        self.scrollable_frame.bind("<Configure>", self._on_frame_resize)

        self._frame_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # mouse wheel
        self.canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind_all("<Button-4>", self._on_mouse_wheel)
        self.canvas.bind_all("<Button-5>", self._on_mouse_wheel)

        self.canvas.bind("<Destroy>", self._on_destroy)

        tk.Label(self.scrollable_frame, text="Welcome back, " + self.username + "!",
                 font=(t.FONT, 20, "bold"), bg="#ecf0f1", fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 5))

    def _on_frame_resize(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_resize(self, event):
        self.canvas.itemconfigure(self._frame_window, width=event.width)

    def open_report_page(self):
        ReportView(self).build_report_content()

    def open_settings_modal(self):
        modal = tk.Toplevel(self.root)
        modal.title("Settings")
        modal.geometry("380x500")
        modal.transient(self.root)
        modal.grab_set()

        tk.Label(modal, text="Signed in as " + self.email, font=(t.FONT, 10, "italic")).pack(pady=(15, 10))

        # preferred currency, the payment window starts with it
        tk.Label(modal, text="Preferred currency", font=(t.FONT, 10, "bold")).pack(anchor="w", padx=30)
        currency_row = tk.Frame(modal)
        currency_row.pack(fill=tk.X, padx=30, pady=(0, 4))
        currency_var = tk.StringVar(value=normalize_currency(get_preferred_currency(self.email)))
        ttk.Combobox(currency_row, textvariable=currency_var, values=CURRENCIES, state="readonly",
                     width=8).pack(side=tk.LEFT)
        currency_status = tk.Label(modal, text="", font=(t.FONT, 9), fg="#27ae60")

        def save_currency():
            if set_preferred_currency(self.email, currency_var.get()):
                currency_status.config(text="Preferred currency set to " + currency_var.get() + ".", fg="#27ae60")
            else:
                currency_status.config(text="Could not save the currency. Please try again.", fg="#c0392b")

        tk.Button(currency_row, text="Save currency", bg=t.PRIMARY, fg="white", font=(t.FONT, 9, "bold"),
                  relief="flat", cursor="hand2", command=save_currency).pack(side=tk.LEFT, padx=(10, 0), ipadx=6)
        currency_status.pack(anchor="w", padx=30, pady=(0, 10))

        if self.role_name == STAFF_ROLE:
            modal.geometry("380x640")
            self._add_staff_venue_settings(modal)

        # Change password
        tk.Label(modal, text="Change password", font=(t.FONT, 11, "bold")).pack(anchor="w", padx=30, pady=(5, 5))

        tk.Label(modal, text="Current password", font=(t.FONT, 10, "bold")).pack(anchor="w", padx=30)
        old_entry = tk.Entry(modal, show="*", width=32)
        old_entry.pack(padx=30, pady=(0, 10))

        tk.Label(modal, text="New password", font=(t.FONT, 10, "bold")).pack(anchor="w", padx=30)
        new_entry = tk.Entry(modal, show="*", width=32)
        new_entry.pack(padx=30, pady=(0, 10))

        tk.Label(modal, text="Confirm new password", font=(t.FONT, 10, "bold")).pack(anchor="w", padx=30)
        confirm_entry = tk.Entry(modal, show="*", width=32)
        confirm_entry.pack(padx=30, pady=(0, 10))

        def save():
            old = old_entry.get()
            new = new_entry.get()
            confirm = confirm_entry.get()
            if not check_login(self.email, old):
                messagebox.showerror("Error", "Your current password is wrong.", parent=modal)
                return
            if len(new) < MIN_PASSWORD_LENGTH:
                messagebox.showerror("Error", "The new password needs at least " + str(MIN_PASSWORD_LENGTH) + " characters.", parent=modal)
                return
            if new != confirm:
                messagebox.showerror("Error", "The two new passwords do not match.", parent=modal)
                return
            update_password(self.email, new)
            messagebox.showinfo("Saved", "Your password has been changed.", parent=modal)
            modal.destroy()

        tk.Button(modal, text="Save new password", bg=t.PRIMARY, fg="white", font=(t.FONT, 10, "bold"),
                  relief="flat", cursor="hand2", command=save).pack(pady=15, ipadx=10, ipady=4)

    # staff choose the venue they work at and the email of the manager, the server checks both
    def _add_staff_venue_settings(self, modal):
        current = get_staff_venue(self.email)
        if not current:
            current = {}
        venues = get_all_venues()
        venue_ids = {}  # "name, address" -> id
        venue_names = []
        for v in venues:
            label = v["name"] + ", " + v["address"]
            if label not in venue_ids:
                venue_names.append(label)
            venue_ids[label] = v["id"]
        current_label = "Choose your venue"
        for label in venue_names:
            if venue_ids[label] == current.get("id"):
                current_label = label
                break

        tk.Label(modal, text="Venue", font=(t.FONT, 10, "bold")).pack(anchor="w", padx=30)
        venue_var = tk.StringVar(value=current_label)
        ttk.Combobox(modal, textvariable=venue_var, values=venue_names, state="readonly", width=40).pack(anchor="w", padx=30)
        tk.Label(modal, text="Manager email", font=(t.FONT, 10, "bold")).pack(anchor="w", padx=30, pady=(6, 0))
        manager_entry = tk.Entry(modal, width=42)
        manager_entry.insert(0, current.get("manager_email", ""))
        manager_entry.pack(anchor="w", padx=30)
        venue_status = tk.Label(modal, text="", font=(t.FONT, 9), wraplength=320, justify="left")

        def save_venue():
            result = set_staff_venue(self.email, venue_ids.get(venue_var.get()), manager_entry.get().strip())
            if result.get("success"):
                color = "#27ae60"
            else:
                color = "#c0392b"
            venue_status.config(text=result.get("message", ""), fg=color)
            if result.get("success"):
                self.on_staff_venue_changed()

        tk.Button(modal, text="Save venue", bg=t.PRIMARY, fg="white", font=(t.FONT, 9, "bold"), relief="flat",
                  cursor="hand2", command=save_venue).pack(anchor="w", padx=30, pady=(6, 2), ipadx=6)
        venue_status.pack(anchor="w", padx=30, pady=(0, 10))

    # the staff screen draws itself again so check in and schedule use the new venue
    def on_staff_venue_changed(self):
        pass

    def _on_mouse_wheel(self, event):
        if not self.canvas.winfo_exists():
            return
        if event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")

    def _on_destroy(self, event):
        if self._clock_timer is not None:
            try:
                self.root.after_cancel(self._clock_timer)
            except Exception:
                pass
            self._clock_timer = None
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")
