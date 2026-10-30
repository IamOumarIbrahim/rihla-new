from datetime import date, timedelta
import tkinter as tk
from tkinter import messagebox
from .users_welcome import BaseWelcomeScreen
from screens.event_screen import show_event_screen
from database import (
    get_all_events, get_bookings_by_customer, cancel_booking, format_ticket_code,
    create_support_ticket, get_support_tickets_by_customer, get_event_capacity
)
from capacity_bar import CapacityBar
import theme as t
import icons as ic
import event_images


def _parse_price(value):
    digits = "".join(c for c in str(value) if c in "0123456789")
    return int(digits) if digits else 0


def _next_date_for_tour(tour):
    today = date.today()
    if tour.get("is_recurring") == "Recurring":
        weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        allowed = {d.strip() for d in (tour.get("recur_day") or "").split(",") if d.strip() in weekday_names}
        if allowed:
            cur = today
            for _ in range(14):
                if weekday_names[cur.weekday()] in allowed:
                    return cur
                cur += timedelta(days=1)
    else:
        try:
            return date.fromisoformat((tour.get("event_datetime") or "")[:10])
        except ValueError:
            pass
    return today


class CustomerWelcomeScreen(BaseWelcomeScreen):
    def __init__(self, root, email):
        super().__init__(root, email, "Customer")
        self.root = root

        self.add_nav_button("My Bookings", self.build_bookings_content, icon="ticket")
        self.add_nav_button("Explore Tours", lambda: self.apply_all_filters(), icon="compass")
        self.add_nav_button("Support", self.build_support_content, icon="chat")

        # Load real vendor-posted events with full dynamic date and time details from database
        db_events = get_all_events()
        self.all_tours = []
        for e in db_events:
            self.all_tours.append({
                "id": e["id"],
                "title": e["title"],
                "category": e["category"] if e["category"] else "General",
                "price": e["price"],
                "event_datetime": e["event_datetime"],
                "time": e["event_datetime"],
                "is_recurring": e["is_recurring"],
                "recur_day": e["recur_day"],
                "recur_time": e["recur_time"],
                "venue_id": e["venue_id"],
                "venue_name": e.get("venue_name") or "Unknown Venue",
                "level": e["is_recurring"],
                "rating": "5.0",
                "desc": e["desc"]
            })

        # Never hide expensive events just because they cost more than 1000 AED.
        self.price_ceiling = max([1000] + [_parse_price(tour["price"]) for tour in self.all_tours])
        self.search_query = ""

        self.current_filters = {
            "category": "All Experiences",
            "max_price": self.price_ceiling,
            "times": [],
            "levels": []
        }

        self.build_customer_content(self.all_tours)

    def build_customer_content(self, tours_to_show):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        tk.Label(self.scrollable_frame, text=f"Marhaba, {self.email.split('@')[0].capitalize()}", font=(t.FONT, 18, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 10))

        search_frame = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        search_frame.pack(fill=tk.X, padx=30, pady=10)


        self.search_entry = tk.Entry(search_frame, font=(t.FONT, 11))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, ipady=5)
        self.search_entry.insert(0, self.search_query or "Search safaris, yacht charters...")
        self.search_entry.bind("<FocusIn>", lambda e: self.search_entry.delete(0, tk.END) if self.search_entry.get() == "Search safaris, yacht charters..." else None)

        search_btn = tk.Button(search_frame, text="Search", bg=t.ACCENT, fg="white", font=(t.FONT, 10, "bold"), relief="flat", command=self.filter_tours)
        search_btn.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=3)
        t.add_hover(search_btn, t.ACCENT, "#e67e22")

        filter_btn = tk.Button(search_frame, text=f"Filter", bg=t.DARK_SOFT, fg="white", font=(t.FONT, 10, "bold"), relief="flat", command=self.open_filter_modal)
        filter_img = ic.get_icon("filter", size=14, color="#ffffff", master=search_frame)
        if filter_img:
            filter_btn.config(image=filter_img, compound=tk.LEFT)
            filter_btn.image = filter_img
        filter_btn.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=3)
        t.add_hover(filter_btn, t.DARK_SOFT, t.DARK)

        cat_frame = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        cat_frame.pack(fill=tk.X, padx=30, pady=10)

        unique_categories = sorted(list(set(tour["category"] for tour in self.all_tours)))
        categories = ["All Experiences"] + unique_categories

        for cat in categories:
            is_active = self.current_filters["category"] == cat
            btn_bg = t.ACCENT if is_active else t.CHIP_BG
            btn_fg = "white" if is_active else t.TEXT
            tk.Button(cat_frame, text=cat, bg=btn_bg, fg=btn_fg, font=(t.FONT, 9, "bold" if is_active else "normal"), relief="flat",
                      command=lambda c=cat: self.filter_by_category(c)).pack(side=tk.LEFT, padx=4, ipady=4, ipadx=8)
        if not tours_to_show:
            tk.Label(self.scrollable_frame, text="No events posted by vendors match your criteria.", font=(t.FONT, 10, "italic"), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=10)
            return

        grid_container = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        grid_container.pack(fill=tk.X, padx=30, pady=10)
        grid_container.columnconfigure(0, weight=1, uniform="col")
        grid_container.columnconfigure(1, weight=1, uniform="col")

        for i, tour in enumerate(tours_to_show):
            row = i // 2
            col = i % 2

            outer = tk.Frame(grid_container, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
            outer.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)
            card = event_images.build_card_shell(outer, tour["id"])

            top_row = tk.Frame(card, bg=t.CARD_BG)
            top_row.pack(fill=tk.X, padx=15, pady=10)

            # Star icon for rating
            star_lbl = tk.Label(top_row, text=f"{ic.emoji('star')} {tour['rating']}", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.ACCENT)
            star_img = ic.get_icon("star", size=14, color=t.ACCENT, master=card)
            if star_img:
                star_lbl.config(image=star_img, compound=tk.LEFT)
                star_lbl.image = star_img
            star_lbl.pack(side=tk.LEFT)

            price_display = tour['price'] if isinstance(tour['price'], str) else f"{tour['price']} AED"
            tk.Label(top_row, text=f"From {price_display}", font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.ACCENT).pack(side=tk.RIGHT)

            tk.Label(card, text=tour["title"], font=(t.FONT, 13, "bold"), bg=t.CARD_BG, fg=t.TEXT, wraplength=280, justify="left").pack(anchor="w", padx=15, pady=2)

            # Schedule info with icons
            sched_frame = tk.Frame(card, bg=t.CARD_BG)
            sched_frame.pack(anchor="w", padx=15, pady=1)

            pin_img = ic.get_icon("map_pin", size=12, color=t.TEXT_MUTED, master=card)
            if pin_img:
                lbl = tk.Label(sched_frame, image=pin_img, bg=t.CARD_BG)
                lbl.image = pin_img
                lbl.pack(side=tk.LEFT)
            tk.Label(sched_frame, text=f"{tour['venue_name']}", font=(t.FONT, 8), bg=t.CARD_BG, fg="#000000").pack(side=tk.LEFT)

            recur_img = ic.get_icon("repeat", size=12, color=t.TEXT_MUTED, master=card)
            if recur_img:
                lbl2 = tk.Label(sched_frame, image=recur_img, bg=t.CARD_BG)
                lbl2.image = recur_img
                lbl2.pack(side=tk.LEFT, padx=(6, 0))
            recur_text = "One-Time Event" if tour['is_recurring'] == "One-Time" else tour['is_recurring']
            tk.Label(sched_frame, text=f"| {recur_text}", font=(t.FONT, 8), bg=t.CARD_BG, fg="#000000").pack(side=tk.LEFT)

            # Live capacity bar
            target_date = _next_date_for_tour(tour)
            cap_info = get_event_capacity(tour['id'], target_date)
            remaining_val = cap_info['remaining'] if cap_info.get('remaining') is not None else cap_info['total']
            cap_box = tk.Frame(card, bg=t.CARD_BG)
            cap_box.pack(anchor="w", padx=15, pady=2)

            users_img = ic.get_icon("users", size=12, color=t.TEXT_MUTED, master=card)
            if users_img:
                ul = tk.Label(cap_box, image=users_img, bg=t.CARD_BG)
                ul.image = users_img
                ul.pack(side=tk.LEFT, padx=(0, 4))
            
            CapacityBar(cap_box, remaining=remaining_val, total=cap_info['total'], width=90, height=12, bg=t.CARD_BG).pack(side=tk.LEFT)

            tk.Label(card, text=tour["desc"], font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED, wraplength=280, justify="left").pack(anchor="w", padx=15, pady=6)

            details_btn = tk.Button(card, text="View Details", bg=t.PRIMARY, fg="white", font=(t.FONT, 10, "bold"), relief="flat",
                                    command=lambda tr=tour: show_event_screen(self.root, self.email, tr))
            details_btn.pack(anchor="w", padx=15, pady=(5, 15), ipadx=10, ipady=5)
            t.add_hover(details_btn, t.PRIMARY, t.PRIMARY_HOVER)

    def build_bookings_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        tk.Label(self.scrollable_frame, text=f"My Bookings", font=(t.FONT, 22, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 5))
        tk.Label(self.scrollable_frame, text="Show your ticket code at the entrance. Each code can be used only once.", font=(t.FONT, 11), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 10))

        bookings = get_bookings_by_customer(self.email)
        if not bookings:
            tk.Label(self.scrollable_frame, text="You have no bookings yet.", font=(t.FONT, 11, "italic"), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=10)
            explore_btn = tk.Button(self.scrollable_frame, text=f"Explore Tours", font=(t.FONT, 10, "bold"), bg=t.PRIMARY, fg="white", relief="flat", command=lambda: self.apply_all_filters())
            explore_btn.pack(anchor="w", padx=30, ipadx=15, ipady=6)
            t.add_hover(explore_btn, t.PRIMARY, t.PRIMARY_HOVER)
            return

        status_colors = {"Confirmed": "#27ae60", "Checked in": t.PRIMARY, "Expired": t.TEXT_MUTED, "Cancelled": "#e74c3c"}

        for booking in bookings:
            card = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
            card.pack(fill=tk.X, padx=30, pady=10, ipady=10)

            top_row = tk.Frame(card, bg=t.CARD_BG)
            top_row.pack(fill=tk.X, padx=15, pady=(5, 0))
            tk.Label(top_row, text=booking["status"].upper(), font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=status_colors.get(booking["status"], t.TEXT_MUTED)).pack(side=tk.LEFT)
            tk.Label(top_row, text=f"{booking['total_price']} AED", font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.ACCENT).pack(side=tk.RIGHT)

            tk.Label(card, text=booking["event_title"], font=(t.FONT, 14, "bold"), bg=t.CARD_BG, fg=t.TEXT, wraplength=600, justify="left").pack(anchor="w", padx=15, pady=2)

            try:
                when = date.fromisoformat(booking["booking_date"]).strftime("%A, %d %b %Y")
            except ValueError:
                when = booking["booking_date"]
            info = f"{when} at {booking['event_time'] or 'TBA'}  |  {booking['venue_name'] or 'Venue to be announced'}  |  {booking['guests']} guest(s)"
            tk.Label(card, text=info, font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=2)

            tk.Label(card, text=f"TICKET CODE", font=(t.FONT, 8, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=(8, 0))
            code_color = t.TEXT if booking["status"] == "Confirmed" else t.TEXT_MUTED
            tk.Label(card, text=format_ticket_code(booking["ticket_code"]), font=("Consolas", 16, "bold"), bg=t.CARD_BG, fg=code_color).pack(anchor="w", padx=15, pady=(0, 5))

            btn_row = tk.Frame(card, bg=t.CARD_BG)
            btn_row.pack(anchor="w", padx=15, pady=(5, 5))

            copy_btn = tk.Button(btn_row, text=f"Copy code", bg=t.CHIP_BG, fg=t.TEXT, font=(t.FONT, 9, "bold"), relief="flat")
            copy_img = ic.get_icon("copy", size=13, color=t.TEXT, master=btn_row)
            if copy_img:
                copy_btn.config(image=copy_img, compound=tk.LEFT)
                copy_btn.image = copy_img
            copy_btn.config(command=lambda code=booking["ticket_code"], b=copy_btn: self.copy_ticket_code(code, b))
            copy_btn.pack(side=tk.LEFT, padx=(0, 10), ipadx=10, ipady=4)
            t.add_hover(copy_btn, t.CHIP_BG, t.CHIP_HOVER)

            if booking["can_cancel"]:
                cancel_btn = tk.Button(btn_row, text=f"Cancel", bg="#e74c3c", fg="white", font=(t.FONT, 9, "bold"), relief="flat",
                                       command=lambda b=booking: self.handle_cancel_booking(b))
                x_img = ic.get_icon("close", size=13, color="#ffffff", master=btn_row)
                if x_img:
                    cancel_btn.config(image=x_img, compound=tk.LEFT)
                    cancel_btn.image = x_img
                cancel_btn.pack(side=tk.LEFT, ipadx=10, ipady=4)
                t.add_hover(cancel_btn, "#e74c3c", "#c0392b")

    def build_support_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        tk.Label(self.scrollable_frame, text="Support", font=(t.FONT, 22, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 5))
        tk.Label(self.scrollable_frame, text="Write to us and our staff will look at your message.", font=(t.FONT, 11), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 10))

        form = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
        form.pack(fill=tk.X, padx=30, pady=10, ipady=10)
        tk.Label(form, text="Subject", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=(10, 2))
        subject_entry = tk.Entry(form, font=(t.FONT, 10))
        subject_entry.pack(fill=tk.X, padx=15)
        tk.Label(form, text="Message", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=(10, 2))
        message_box = tk.Text(form, height=5, font=(t.FONT, 10))
        message_box.pack(fill=tk.X, padx=15)

        def send():
            result = create_support_ticket(self.email, subject_entry.get(), message_box.get("1.0", "end"))
            if result["success"]:
                messagebox.showinfo("Sent", result["message"])
                self.build_support_content()
            else:
                messagebox.showerror("Cannot send", result["message"])

        send_btn = tk.Button(form, text=f"Send message", font=(t.FONT, 10, "bold"), bg=t.PRIMARY, fg="white", relief="flat", command=send)
        send_btn.pack(anchor="w", padx=15, pady=(10, 5), ipadx=15, ipady=6)
        t.add_hover(send_btn, t.PRIMARY, t.PRIMARY_HOVER)

        tickets = get_support_tickets_by_customer(self.email)
        if tickets:
            tk.Label(self.scrollable_frame, text="Your messages", font=(t.FONT, 14, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(15, 5))
        for ticket in tickets:
            card = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
            card.pack(fill=tk.X, padx=30, pady=6, ipady=6)
            color = "#27ae60" if ticket["status"] == "Resolved" else t.ACCENT
            tk.Label(card, text=f"{ticket['status'].upper()}  |  {ticket['created_at']}", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=color).pack(anchor="w", padx=15, pady=(6, 0))
            tk.Label(card, text=ticket["subject"], font=(t.FONT, 12, "bold"), bg=t.CARD_BG, fg=t.TEXT, wraplength=650, justify="left").pack(anchor="w", padx=15, pady=2)
            tk.Label(card, text=ticket["message"], font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED, wraplength=650, justify="left").pack(anchor="w", padx=15, pady=2)

    def copy_ticket_code(self, code, button):
        self.root.clipboard_clear()
        self.root.clipboard_append(code)
        button.config(text=f"Copied!")

    def handle_cancel_booking(self, booking):
        if not messagebox.askyesno("Cancel booking", f"Cancel your booking for {booking['event_title']}?\n\nThe ticket code will stop working."):
            return
        result = cancel_booking(booking["id"], self.email)
        if result["success"]:
            messagebox.showinfo("Booking cancelled", result["message"])
        else:
            messagebox.showerror("Cannot cancel", result["message"])
        self.build_bookings_content()

    def open_filter_modal(self):
        modal = tk.Toplevel(self.root)
        modal.title("Filter Excursions")
        modal.geometry("440x520")
        modal.configure(bg=t.CARD_BG)
        modal.resizable(False, False)

        modal.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (440 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (520 // 2)
        modal.geometry(f"+{x}+{y}")

        tk.Label(modal, text="Filter Excursions", font=(t.FONT, 18, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 10))

        content_frame = tk.Frame(modal, bg=t.CARD_BG)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=5)

        tk.Label(content_frame, text="Maximum Price (AED)", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(5, 5))

        price_slider = tk.Scale(content_frame, from_=50, to=self.price_ceiling, orient=tk.HORIZONTAL, bg=t.FIELD_BG, fg=t.TEXT, font=(t.FONT, 9), highlightthickness=1, highlightbackground=t.BORDER, troughcolor=t.BORDER)
        price_slider.set(self.current_filters["max_price"])
        price_slider.pack(fill=tk.X, pady=5)

        btn_frame = tk.Frame(modal, bg=t.CARD_BG)
        btn_frame.pack(fill=tk.X, padx=30, pady=20)

        def apply_filters():
            self.current_filters["max_price"] = price_slider.get()
            modal.destroy()
            self.apply_all_filters()

        def reset_filters():
            price_slider.set(self.price_ceiling)
            self.current_filters = {"category": "All Experiences", "max_price": self.price_ceiling, "times": [], "levels": []}
            modal.destroy()
            self.apply_all_filters()

        reset_btn = tk.Button(btn_frame, text="Reset", font=(t.FONT, 10, "bold"), bg=t.CHIP_BG, fg=t.TEXT, relief="flat", command=reset_filters)
        reset_btn.pack(side=tk.LEFT, ipadx=15, ipady=8)
        t.add_hover(reset_btn, t.CHIP_BG, t.CHIP_HOVER)

        apply_btn = tk.Button(btn_frame, text="Apply Filters", font=(t.FONT, 10, "bold"), bg=t.PRIMARY, fg="white", relief="flat", command=apply_filters)
        apply_btn.pack(side=tk.RIGHT, ipadx=20, ipady=8)
        t.add_hover(apply_btn, t.PRIMARY, t.PRIMARY_HOVER)

    def apply_all_filters(self):
        filtered = self.all_tours

        cat = self.current_filters["category"]
        if cat != "All Experiences":
            filtered = [tour for tour in filtered if tour["category"] == cat]

        max_p = self.current_filters["max_price"]

        def parse_price(p_str):
            try:
                digits = "".join([c for c in str(p_str) if c.isdigit()])
                return int(digits) if digits else 0
            except ValueError:
                return 0

        filtered = [tour for tour in filtered if parse_price(tour["price"]) <= max_p]

        query = self.search_query.lower()
        if query:
            filtered = [tour for tour in filtered if query in tour["title"].lower() or query in tour["category"].lower() or query in (tour["desc"] or "").lower()]

        self.build_customer_content(filtered)

    def filter_tours(self):
        query = self.search_entry.get().strip()
        if query.lower() == "search safaris, yacht charters...":
            query = ""
        self.search_query = query
        self.apply_all_filters()

    def filter_by_category(self, category):
        self.current_filters["category"] = category
        self.apply_all_filters()


def show_customer_welcome(root, email, view=None):
    screen = CustomerWelcomeScreen(root, email)
    if view == "bookings":
        screen.build_bookings_content()
