import tkinter as tk
from tkinter import messagebox
from .users_welcome import BaseWelcomeScreen
import theme as t
import icons as ic
from datetime import date
from database import (
    get_all_venues, get_events_by_venue, verify_ticket_code,
    get_open_support_tickets, resolve_support_ticket, get_events_today
)


class StaffWelcomeScreen(BaseWelcomeScreen):
    def __init__(self, root, email):
        super().__init__(root, email, "Staff")
        self.root = root

        # Staff-specific nav items
        self.add_nav_button("Ticket Scanner", self.build_scanner_content, icon="scan")
        self.add_nav_button("Support Tickets", self.build_support_content, icon="chat")
        self.add_nav_button("Schedule", self.build_schedule_content, icon="calendar")

        # Render Ticket Scanner content by default
        self.build_scanner_content()

    def build_scanner_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        tk.Label(self.scrollable_frame, text=f"Venue Ticket Scanner", font=(t.FONT, 22, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 5))

        # Card container for scanner interface
        card = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
        card.pack(fill=tk.X, padx=30, pady=10, ipady=20, ipadx=20)

        # 1. Venue Selection
        tk.Label(card, text=f"SELECT VENUE", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=20, pady=(10, 5))

        venues = get_all_venues()
        venue_dict = {f"{v['name']}, {v['address']}": v['id'] for v in venues} if venues else {}
        venue_options = list(venue_dict.keys()) if venue_dict else ["No venues available"]

        selected_venue_str = tk.StringVar(card)
        selected_venue_str.set(venue_options[0] if venue_options else "")

        # 2. Event Selection Container (Dynamic)
        tk.Label(card, text=f"SELECT EVENT", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=20, pady=(10, 5))
        
        event_var = tk.StringVar(card)
        event_titles = {}  # menu text -> event title, used to check the ticket belongs to the chosen event
        event_menu_holder = tk.Frame(card, bg=t.CARD_BG)
        event_menu_holder.pack(fill=tk.X, padx=20, pady=(0, 10))

        def update_event_options(*args):
            for widget in event_menu_holder.winfo_children():
                widget.destroy()
            
            event_var.set("")
            event_titles.clear()
            v_str = selected_venue_str.get()
            if not v_str or v_str not in venue_dict:
                tk.Label(event_menu_holder, text="Select a valid venue first", font=(t.FONT, 10, "italic"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w")
                return

            venue_id = venue_dict[v_str]
            events = get_events_by_venue(venue_id)
            
            if not events:
                tk.Label(event_menu_holder, text="No events found for this venue", font=(t.FONT, 10, "italic"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w")
                return

            event_options = [f"{e['title']}, {e['event_datetime']}" for e in events]
            event_var.set(event_options[0])
            event_titles.update({f"{e['title']}, {e['event_datetime']}": e["title"] for e in events})

            event_menu = tk.OptionMenu(event_menu_holder, event_var, *event_options)
            event_menu.config(font=(t.FONT, 11), bg=t.FIELD_BG, relief="solid", bd=1, highlightthickness=0)
            event_menu.pack(fill=tk.X, ipady=5)

        selected_venue_str.trace_add("write", update_event_options)

        venue_menu = tk.OptionMenu(card, selected_venue_str, *venue_options)
        venue_menu.config(font=(t.FONT, 11), bg=t.FIELD_BG, relief="solid", bd=1, highlightthickness=0)
        venue_menu.pack(fill=tk.X, padx=20, pady=(0, 10), ipady=5)

        # Initial call to populate events for the first venue
        update_event_options()

        # 3. Ticket Input Field
        tk.Label(card, text=f"16-DIGIT ENTRY TICKET CODE", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=20, pady=(10, 5))

        code_entry = tk.Entry(card, font=(t.FONT, 14), bg=t.FIELD_BG, relief="solid", bd=1, justify="center")
        code_entry.pack(fill=tk.X, padx=20, pady=(0, 15), ipady=8)
        code_entry.focus_set()

        result_label = tk.Label(card, text="", font=(t.FONT, 11, "bold"), bg=t.CARD_BG)
        result_label.pack(anchor="w", padx=20, pady=(5, 10))

        def process_scan(event=None):
            code = code_entry.get().strip()
            if len(code) != 16 or not code.isdigit():
                result_label.config(text=f"{ic.emoji('alert')} Error: Ticket code must be exactly 16 digits.", fg="#e74c3c")
                return

            expected_title = event_titles.get(event_var.get())
            if not expected_title:
                result_label.config(text=f"{ic.emoji('alert')} Error: Select a venue and an event first.", fg="#e74c3c")
                return

            res = verify_ticket_code(code, expected_title)
            if res["success"]:
                result_label.config(text=f"{ic.emoji('check')} OK: {res['message']}", fg="#27ae60")
                code_entry.delete(0, tk.END)
            else:
                result_label.config(text=f"{ic.emoji('cross')} Failed: {res['message']}", fg="#e74c3c")

        code_entry.bind("<Return>", process_scan)

        scan_btn = tk.Button(card, text=f"Validate", font=(t.FONT, 11, "bold"), bg=t.PRIMARY, fg="white", relief="flat", command=process_scan)
        scan_btn.pack(fill=tk.X, padx=20, pady=10, ipady=10)
        t.add_hover(scan_btn, t.PRIMARY, t.PRIMARY_HOVER)

        tip_text = tk.Label(card, text="Test Ticket Code: 1234567890123456", font=(t.FONT, 9, "italic"), bg=t.CARD_BG, fg=t.TEXT_MUTED)
        tip_text.pack(anchor="w", padx=20, pady=(10, 0))

    def build_support_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        tk.Label(self.scrollable_frame, text=f"Support Tickets", font=(t.FONT, 22, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 10))
        self.render_support_list()



    def build_schedule_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        tk.Label(self.scrollable_frame, text=f"Staff Schedule", font=(t.FONT, 22, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 10))
        self.render_today_schedule()


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
            tk.Label(card, text=ticket["message"], font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT, wraplength=650, justify="left").pack(anchor="w", padx=15, pady=4)
            resolve_btn = tk.Button(card, text=f"{ic.emoji('check')} Mark resolved", font=(t.FONT, 9, "bold"), bg=t.PRIMARY, fg="white", relief="flat",
                                    command=lambda tid=ticket["id"]: self.handle_resolve_ticket(tid))
            resolve_btn.pack(anchor="w", padx=15, pady=(4, 8), ipadx=10, ipady=4)

    def handle_resolve_ticket(self, ticket_id):
        resolve_support_ticket(ticket_id, self.email)
        self.build_support_content()

    def render_today_schedule(self):
        tk.Label(self.scrollable_frame, text=f"" + date.today().strftime("%A, %d %B %Y"), font=(t.FONT, 11), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 10))
        events = get_events_today()
        if not events:
            tk.Label(self.scrollable_frame, text="No events are running today.", font=(t.FONT, 11, "italic"), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30)
            return
        for ev in events:
            card = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
            card.pack(fill=tk.X, padx=30, pady=8, ipady=8)
            tk.Label(card, text=ev["title"], font=(t.FONT, 13, "bold"), bg=t.CARD_BG, fg=t.TEXT, wraplength=650, justify="left").pack(anchor="w", padx=15, pady=(8, 2))
            tk.Label(card, text=f"{ic.emoji('clock')} {ev['time'] or 'TBA'}  |  {ev['venue_name'] or 'Venue to be announced'}", font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15)
            tk.Label(card, text=f"{ic.emoji('ticket')} Bookings: {ev['bookings']} |   {ic.emoji('users')} Expected guests: {ev['guests']}  |  {ic.emoji('check')} Checked in: {ev['checked_in']}", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=15, pady=(4, 8))


def show_staff_welcome(root, email):
    StaffWelcomeScreen(root, email)