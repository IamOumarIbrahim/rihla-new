import tkinter as tk
from tkinter import messagebox
from .users_welcome import BaseWelcomeScreen
import theme as t
import icons as ic
from map_link import venue_label
from digit_boxes import DigitBoxes
from .dispatch_view import ROW_EVEN, ROW_ODD
from .cancellation import page_header
from datetime import date
from database import (
    get_staff_venue, get_events_by_venue, verify_ticket_code,
    get_open_support_tickets, resolve_support_ticket, get_events_today
)

SCHEDULE_HEADING_BG = "#e5e8e8"
# Columns of today's schedule table: (heading, anchor, grid weight). Every row is at the staff member's venue.
SCHEDULE_COLUMNS = [
    ("Event", "w", 3),
    ("Time", "center", 1),
    ("Bookings", "center", 1),
    ("Expected guests", "center", 1),
    ("Checked in", "center", 1),
]
# The demo ticket from server/database_core.py is for the New year dinner at Burj Khalifa.
DEMO_TICKET_HINT = "Demo ticket (Burj Khalifa staff): 1234 5678 9012 3456"


class StaffWelcomeScreen(BaseWelcomeScreen):
    def __init__(self, root, email):
        super().__init__(root, email, "Staff")
        self.root = root

        # Staff-specific nav items: check-in and today's schedule share one page for the staff member's venue
        self.add_nav_button("Venue Operations", self.build_operations_content, icon="scan")
        self.add_nav_button("Support Tickets", self.build_support_content, icon="chat")

        # Render Venue Operations content by default
        self.build_operations_content()

    def on_staff_venue_changed(self):
        self.build_operations_content()

    def build_operations_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        page_header(self.scrollable_frame, "Venue Operations", self.build_operations_content, pady=(20, 5))

        # The server decides which venue this account works at; staff change it in Settings.
        venue = get_staff_venue(self.email)
        if not venue:
            tk.Label(self.scrollable_frame, text="Your account is not assigned to a venue yet. Choose your venue in Settings.",
                     font=(t.FONT, 11, "italic"), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=10)
            return

        venue_row = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        venue_row.pack(fill=tk.X, padx=30, pady=(0, 5))
        venue_label(venue_row, f"{venue['name']}, {venue['address']}", venue.get("maps_url"),
                    font=(t.FONT, 12, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(side=tk.LEFT)
        tk.Label(venue_row, text=f"Manager: {venue['manager_email'] or 'not set'}", font=(t.FONT, 10),
                 bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(side=tk.RIGHT)

        self.build_checkin_card(venue)

        tk.Label(self.scrollable_frame, text="Today's Schedule", font=(t.FONT, 16, "bold"), bg=t.PAGE_BG,
                 fg=t.TEXT).pack(anchor="w", padx=30, pady=(15, 2))
        self.schedule_holder = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        self.schedule_holder.pack(fill=tk.X)
        self.render_today_schedule()

    def build_checkin_card(self, venue):
        # Card container for scanner interface
        card = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
        card.pack(fill=tk.X, padx=30, pady=10, ipady=20, ipadx=20)

        tk.Label(card, text="Ticket Check-in", font=(t.FONT, 14, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=20, pady=(10, 0))

        # 1. Event Selection: only the events at this staff member's venue
        tk.Label(card, text=f"SELECT EVENT", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=20, pady=(10, 5))

        event_var = tk.StringVar(card)
        event_titles = {}  # menu text -> event title, used to check the ticket belongs to the chosen event
        events = get_events_by_venue(venue["id"])
        if events:
            event_options = [f"{e['title']}, {e['event_datetime']}" for e in events]
            event_var.set(event_options[0])
            event_titles.update({f"{e['title']}, {e['event_datetime']}": e["title"] for e in events})
            event_menu = tk.OptionMenu(card, event_var, *event_options)
            event_menu.config(font=(t.FONT, 11), bg=t.FIELD_BG, relief="solid", bd=1, highlightthickness=0, anchor="w")
            event_menu.pack(fill=tk.X, padx=20, pady=(0, 10), ipady=5)
        else:
            tk.Label(card, text="No events found for your venue", font=(t.FONT, 10, "italic"), bg=t.CARD_BG,
                     fg=t.TEXT_MUTED).pack(anchor="w", padx=20, pady=(0, 10))

        # 2. Ticket Input Field
        tk.Label(card, text=f"16-DIGIT ENTRY TICKET CODE", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=20, pady=(10, 5))

        # 4 groups of 4 boxes: digits only, the cursor moves on after every digit
        code_boxes = DigitBoxes(card, groups=4, group_size=4, font_size=16,
                                on_complete=lambda code: scan_btn.focus_set(),
                                on_change=lambda code: result_label.config(text=""))
        code_boxes.pack(anchor="w", padx=20, pady=(0, 6))

        code_boxes.focus_first()

        result_label = tk.Label(card, text="", font=(t.FONT, 11, "bold"), bg=t.CARD_BG)
        result_label.pack(anchor="w", padx=20, pady=(5, 10))

        def process_scan(event=None):
            code = code_boxes.get()
            if not code_boxes.is_complete():
                code_boxes.set_error(True)
                result_label.config(text=f"{ic.emoji('alert')} Error: Ticket code must be exactly 16 digits ({len(code)} entered).", fg="#e74c3c")
                return

            expected_title = event_titles.get(event_var.get())
            if not expected_title:
                result_label.config(text=f"{ic.emoji('alert')} Error: Select an event first.", fg="#e74c3c")
                return

            # The server refuses tickets for events at any other venue.
            res = verify_ticket_code(code, expected_title, staff_email=self.email)
            if res["success"]:
                result_label.config(text=f"{ic.emoji('check')} OK: {res['message']}", fg="#27ae60")
                code_boxes.clear()
                self.render_today_schedule()  # the Checked in column moves on
            else:
                result_label.config(text=f"{ic.emoji('cross')} Failed: {res['message']}", fg="#e74c3c")
                code_boxes.set_error(True)

        code_boxes.bind_all_boxes("<Return>", process_scan)

        scan_btn = tk.Button(card, text=f"Validate", font=(t.FONT, 11, "bold"), bg=t.PRIMARY, fg="white", relief="flat", command=process_scan)
        scan_btn.pack(fill=tk.X, padx=20, pady=10, ipady=10)
        scan_btn.bind("<Return>", process_scan)
        t.add_hover(scan_btn, t.PRIMARY, t.PRIMARY_HOVER)

        tip_text = tk.Label(card, text=DEMO_TICKET_HINT, font=(t.FONT, 9, "italic"), bg=t.CARD_BG, fg=t.TEXT_MUTED)
        tip_text.pack(anchor="w", padx=20, pady=(10, 0))

    def build_support_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        tk.Label(self.scrollable_frame, text=f"Support Tickets", font=(t.FONT, 22, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 10))
        self.render_support_list()

    def render_support_list(self):
        tickets = get_open_support_tickets()
        if not tickets:
            tk.Label(self.scrollable_frame, text="No open support tickets at the moment.", font=(t.FONT, 11), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30)
            return
        for ticket in tickets:
            card = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
            card.pack(fill=tk.X, padx=30, pady=8, ipady=8)
            tk.Label(card, text=ticket["subject"], font=(t.FONT, 13, "bold"), bg=t.CARD_BG, fg=t.TEXT, wraplength=650, justify="left").pack(anchor="w", padx=15, pady=(8, 2))
            tk.Label(card, text=f"From {ticket['customer_email']}  |  {ticket['created_at']}", font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15)
            if ticket.get("event_title"):
                tk.Label(card, text=f"Event: {ticket['event_title']}", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15)
            tk.Label(card, text=ticket["message"], font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT, wraplength=650, justify="left").pack(anchor="w", padx=15, pady=4)
            resolve_btn = tk.Button(card, text=f"{ic.emoji('check')} Mark resolved", font=(t.FONT, 9, "bold"), bg=t.PRIMARY, fg="white", relief="flat",
                                    command=lambda tid=ticket["id"]: self.handle_resolve_ticket(tid))
            resolve_btn.pack(anchor="w", padx=15, pady=(4, 8), ipadx=10, ipady=4)

    def handle_resolve_ticket(self, ticket_id):
        resolve_support_ticket(ticket_id, self.email)
        self.build_support_content()

    def render_today_schedule(self):
        holder = self.schedule_holder
        for widget in holder.winfo_children():
            widget.destroy()
        tk.Label(holder, text=date.today().strftime("%A, %d %B %Y"), font=(t.FONT, 11), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 10))
        events = get_events_today(self.email)  # the server only returns this staff member's venue
        if not events:
            tk.Label(holder, text="No events are running at your venue today.", font=(t.FONT, 11, "italic"), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30)
            return
        # Earliest first; events without a time go to the bottom
        events = sorted(events, key=lambda ev: (not ev['time'], ev['time'] or "", ev['title']))

        # A grid of labels; colours and fonts match the dispatch tables.
        table = tk.Frame(holder, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
        table.pack(fill=tk.X, padx=30, pady=(0, 10))

        for col, (heading, anchor, weight) in enumerate(SCHEDULE_COLUMNS):
            tk.Label(table, text=heading, font=(t.FONT, 10, "bold"), bg=SCHEDULE_HEADING_BG, fg=t.TEXT, anchor=anchor,
                     padx=10, pady=6).grid(row=0, column=col, sticky="nsew")
            table.grid_columnconfigure(col, weight=weight)

        for i, ev in enumerate(events, start=1):
            bg = ROW_ODD if i % 2 == 0 else ROW_EVEN
            values = [ev['title'], ev['time'] or "TBA", ev['bookings'], ev['guests'], ev['checked_in']]
            for col, value in enumerate(values):
                tk.Label(table, text=value, wraplength=260 if col == 0 else 0, justify="left", bg=bg,
                         anchor=SCHEDULE_COLUMNS[col][1], padx=10, pady=5, font=(t.FONT, 10), fg=t.TEXT
                         ).grid(row=i, column=col, sticky="nsew")


def show_staff_welcome(root, email):
    StaffWelcomeScreen(root, email)
