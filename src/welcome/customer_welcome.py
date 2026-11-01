from datetime import date, timedelta
import tkinter as tk
from tkinter import messagebox, ttk
from .users_welcome import BaseWelcomeScreen
from .cancellation import page_header, policy_line, cancelled_line, confirm_own_cancel
from screens.event_screen import show_event_screen
from database import (
    get_all_events, get_bookings_by_customer, cancel_booking, format_ticket_code,
    create_support_ticket, get_support_tickets_by_customer, get_event_capacity,
    get_my_experiences, submit_review, get_event_ratings
)
from capacity_bar import CapacityBar
import theme as t
import icons as ic
import event_images
from map_link import venue_label


MAX_REVIEW_COMMENT = 500
SEARCH_HINT = "Search safaris, yacht charters..."


def _parse_price(value):
    digits = ""
    for c in str(value):
        if c in "0123456789":
            digits = digits + c
    if digits:
        return int(digits)
    return 0


# next date the tour happens (for the capacity bar on the card)
def _next_date_for_tour(tour):
    today = date.today()
    if tour.get("is_recurring") == "Recurring":
        weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        recur_day = tour.get("recur_day")
        if not recur_day:
            recur_day = ""
        allowed = []
        for d in recur_day.split(","):
            if d.strip() in weekday_names:
                allowed.append(d.strip())
        if allowed:
            cur = today
            for k in range(14):
                if weekday_names[cur.weekday()] in allowed:
                    return cur
                cur += timedelta(days=1)
    else:
        dt = tour.get("event_datetime")
        if not dt:
            dt = ""
        try:
            return date.fromisoformat(dt[:10])
        except ValueError:
            pass
    return today


class CustomerWelcomeScreen(BaseWelcomeScreen):
    def __init__(self, root, email):
        BaseWelcomeScreen.__init__(self, root, email, "Customer")
        self.root = root

        self.add_nav_button("My Bookings", self.build_bookings_content, icon="ticket")
        self.add_nav_button("My Experiences", self.build_experiences_content, icon="star")
        self.add_nav_button("Explore Tours", self.apply_all_filters, icon="compass")
        self.add_nav_button("Support", self.build_support_content, icon="chat")

        # the events the vendors posted, with all the date and time details
        db_events = get_all_events()
        self.all_tours = []
        for e in db_events:
            category = e["category"]
            if not category:
                category = "General"
            venue_name = e.get("venue_name")
            if not venue_name:
                venue_name = "Unknown Venue"
            maps_url = e.get("maps_url")
            if not maps_url:
                maps_url = ""
            self.all_tours.append({
                "id": e["id"],
                "title": e["title"],
                "category": category,
                "price": e["price"],
                "event_datetime": e["event_datetime"],
                "time": e["event_datetime"],
                "is_recurring": e["is_recurring"],
                "recur_day": e["recur_day"],
                "recur_time": e["recur_time"],
                "venue_id": e["venue_id"],
                "venue_name": venue_name,
                "maps_url": maps_url,
                "level": e["is_recurring"],
                "rating": "0.0",
                "desc": e["desc"]
            })

        # dont hide expensive events just because they cost more than 1000 AED
        self.price_ceiling = 1000
        for tour in self.all_tours:
            if _parse_price(tour["price"]) > self.price_ceiling:
                self.price_ceiling = _parse_price(tour["price"])
        self.search_query = ""

        self.current_filters = {
            "category": "All Experiences",
            "max_price": self.price_ceiling,
            "times": [],
            "levels": []
        }

        self.build_customer_content(self.all_tours)

    # gets the average rating of every event from the reviews (0.0 if it has no reviews)
    def _refresh_ratings(self):
        ratings = get_event_ratings()
        for tour in self.all_tours:
            info = ratings.get(str(tour["id"]))
            if info:
                tour["rating"] = format(info['average'], ".1f")
            else:
                tour["rating"] = "0.0"

    def _clear_search_hint(self, event):
        if self.search_entry.get() == SEARCH_HINT:
            self.search_entry.delete(0, tk.END)

    def build_customer_content(self, tours_to_show):
        self._refresh_ratings()
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        tk.Label(self.scrollable_frame, text="Marhaba, " + self.email.split('@')[0].capitalize(), font=(t.FONT, 18, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 10))

        search_frame = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        search_frame.pack(fill=tk.X, padx=30, pady=10)


        self.search_entry = tk.Entry(search_frame, font=(t.FONT, 11))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, ipady=5)
        if self.search_query:
            self.search_entry.insert(0, self.search_query)
        else:
            self.search_entry.insert(0, SEARCH_HINT)
        self.search_entry.bind("<FocusIn>", self._clear_search_hint)

        search_btn = tk.Button(search_frame, text="Search", bg=t.ACCENT, fg="white", font=(t.FONT, 10, "bold"), relief="flat", command=self.filter_tours)
        search_btn.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=3)
        t.add_hover(search_btn, t.ACCENT, "#e67e22")

        filter_btn = tk.Button(search_frame, text="Filter", bg=t.DARK_SOFT, fg="white", font=(t.FONT, 10, "bold"), relief="flat", command=self.open_filter_modal)
        filter_img = ic.get_icon("filter", size=14, color="#ffffff", master=search_frame)
        if filter_img:
            filter_btn.config(image=filter_img, compound=tk.LEFT)
            filter_btn.image = filter_img
        filter_btn.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=3)
        t.add_hover(filter_btn, t.DARK_SOFT, t.DARK)

        # category buttons
        cat_frame = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        cat_frame.pack(fill=tk.X, padx=30, pady=10)

        unique_categories = []
        for tour in self.all_tours:
            if tour["category"] not in unique_categories:
                unique_categories.append(tour["category"])
        unique_categories.sort()
        categories = ["All Experiences"] + unique_categories

        for cat in categories:
            if self.current_filters["category"] == cat:
                btn_bg = t.ACCENT
                btn_fg = "white"
                weight = "bold"
            else:
                btn_bg = t.CHIP_BG
                btn_fg = t.TEXT
                weight = "normal"

            def pick_category(c=cat):
                self.filter_by_category(c)
            tk.Button(cat_frame, text=cat, bg=btn_bg, fg=btn_fg, font=(t.FONT, 9, weight), relief="flat",
                      command=pick_category).pack(side=tk.LEFT, padx=4, ipady=4, ipadx=8)
        if not tours_to_show:
            tk.Label(self.scrollable_frame, text="No events posted by vendors match your criteria.", font=(t.FONT, 10, "italic"), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=10)
            return

        # 2 cards in every row
        grid_container = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        grid_container.pack(fill=tk.X, padx=30, pady=10)
        grid_container.columnconfigure(0, weight=1, uniform="col")
        grid_container.columnconfigure(1, weight=1, uniform="col")

        for i in range(len(tours_to_show)):
            tour = tours_to_show[i]
            row = i // 2
            col = i % 2

            outer = tk.Frame(grid_container, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
            outer.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)
            card = event_images.build_card_shell(outer, tour["id"])

            top_row = tk.Frame(card, bg=t.CARD_BG)
            top_row.pack(fill=tk.X, padx=15, pady=10)

            # rating with a star
            star_lbl = tk.Label(top_row, text=ic.emoji("star") + " " + format(float(tour['rating']), ".1f") + "/5.0", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.ACCENT)
            star_img = ic.get_icon("star", size=14, color=t.ACCENT, master=card)
            if star_img:
                star_lbl.config(image=star_img, compound=tk.LEFT)
                star_lbl.image = star_img
            star_lbl.pack(side=tk.LEFT)

            if isinstance(tour['price'], str):
                price_display = tour['price']
            else:
                price_display = str(tour['price']) + " AED"
            tk.Label(top_row, text="From " + price_display, font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.ACCENT).pack(side=tk.RIGHT)

            tk.Label(card, text=tour["title"], font=(t.FONT, 13, "bold"), bg=t.CARD_BG, fg=t.TEXT, wraplength=280, justify="left").pack(anchor="w", padx=15, pady=2)

            # venue and schedule with the icons
            sched_frame = tk.Frame(card, bg=t.CARD_BG)
            sched_frame.pack(anchor="w", padx=15, pady=1)

            pin_img = ic.get_icon("map_pin", size=12, color=t.TEXT_MUTED, master=card)
            if pin_img:
                lbl = tk.Label(sched_frame, image=pin_img, bg=t.CARD_BG)
                lbl.image = pin_img
                lbl.pack(side=tk.LEFT)
            venue_label(sched_frame, str(tour['venue_name']), tour.get("maps_url"), font=(t.FONT, 8), bg=t.CARD_BG, fg="#000000").pack(side=tk.LEFT)

            recur_img = ic.get_icon("repeat", size=12, color=t.TEXT_MUTED, master=card)
            if recur_img:
                lbl2 = tk.Label(sched_frame, image=recur_img, bg=t.CARD_BG)
                lbl2.image = recur_img
                lbl2.pack(side=tk.LEFT, padx=(6, 0))
            if tour['is_recurring'] == "One-Time":
                recur_text = "One-Time Event"
            else:
                recur_text = tour['is_recurring']
            tk.Label(sched_frame, text="| " + str(recur_text), font=(t.FONT, 8), bg=t.CARD_BG, fg="#000000").pack(side=tk.LEFT)

            # capacity bar with the real seats left
            target_date = _next_date_for_tour(tour)
            cap_info = get_event_capacity(tour['id'], target_date)
            if cap_info.get('remaining') is not None:
                remaining_val = cap_info['remaining']
            else:
                remaining_val = cap_info['total']
            cap_box = tk.Frame(card, bg=t.CARD_BG)
            cap_box.pack(anchor="w", padx=15, pady=2)

            users_img = ic.get_icon("users", size=12, color=t.TEXT_MUTED, master=card)
            if users_img:
                ul = tk.Label(cap_box, image=users_img, bg=t.CARD_BG)
                ul.image = users_img
                ul.pack(side=tk.LEFT, padx=(0, 4))

            CapacityBar(cap_box, remaining=remaining_val, total=cap_info['total'], width=90, height=12, bg=t.CARD_BG).pack(side=tk.LEFT)

            tk.Label(card, text=tour["desc"], font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED, wraplength=280, justify="left").pack(anchor="w", padx=15, pady=6)

            def open_details(tr=tour):
                show_event_screen(self.root, self.email, tr)

            details_btn = tk.Button(card, text="View Details", bg=t.PRIMARY, fg="white", font=(t.FONT, 10, "bold"), relief="flat",
                                    command=open_details)
            details_btn.pack(anchor="w", padx=15, pady=(5, 15), ipadx=10, ipady=5)
            t.add_hover(details_btn, t.PRIMARY, t.PRIMARY_HOVER)

    def build_bookings_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        page_header(self.scrollable_frame, "My Bookings", self.build_bookings_content)
        tk.Label(self.scrollable_frame, text="Show your ticket code at the entrance. Each code can be used only once.", font=(t.FONT, 11), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 10))

        bookings = get_bookings_by_customer(self.email)
        if not bookings:
            tk.Label(self.scrollable_frame, text="You have no bookings yet.", font=(t.FONT, 11, "italic"), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=10)
            explore_btn = tk.Button(self.scrollable_frame, text="Explore Tours", font=(t.FONT, 10, "bold"), bg=t.PRIMARY, fg="white", relief="flat", command=self.apply_all_filters)
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
            tk.Label(top_row, text=str(booking['total_price']) + " AED", font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.ACCENT).pack(side=tk.RIGHT)

            tk.Label(card, text=booking["event_title"], font=(t.FONT, 14, "bold"), bg=t.CARD_BG, fg=t.TEXT, wraplength=600, justify="left").pack(anchor="w", padx=15, pady=2)

            try:
                when = date.fromisoformat(booking["booking_date"]).strftime("%A, %d %b %Y")
            except ValueError:
                when = booking["booking_date"]
            time_text = booking['event_time']
            if not time_text:
                time_text = 'TBA'
            venue = booking['venue_name']
            if not venue:
                venue = 'Venue to be announced'
            info = str(when) + " at " + str(time_text) + "  |  " + str(venue) + "  |  " + str(booking['guests']) + " guest(s)"
            tk.Label(card, text=info, font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=2)

            tk.Label(card, text="TICKET CODE", font=(t.FONT, 8, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=(8, 0))
            if booking["status"] == "Confirmed":
                code_color = t.TEXT
            else:
                code_color = t.TEXT_MUTED
            tk.Label(card, text=format_ticket_code(booking["ticket_code"]), font=("Consolas", 16, "bold"), bg=t.CARD_BG, fg=code_color).pack(anchor="w", padx=15, pady=(0, 5))
            if booking["status"] == "Cancelled":
                tk.Label(card, text=cancelled_line(booking, self.email), font=(t.FONT, 9), bg=t.CARD_BG, fg="#c0392b",
                         wraplength=600, justify="left").pack(anchor="w", padx=15, pady=(0, 4))
            elif booking["status"] == "Confirmed":
                tk.Label(card, text=policy_line(booking), font=(t.FONT, 9, "italic"), bg=t.CARD_BG,
                         fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=(0, 4))

            btn_row = tk.Frame(card, bg=t.CARD_BG)
            btn_row.pack(anchor="w", padx=15, pady=(5, 5))

            copy_btn = tk.Button(btn_row, text="Copy code", bg=t.CHIP_BG, fg=t.TEXT, font=(t.FONT, 9, "bold"), relief="flat")
            copy_img = ic.get_icon("copy", size=13, color=t.TEXT, master=btn_row)
            if copy_img:
                copy_btn.config(image=copy_img, compound=tk.LEFT)
                copy_btn.image = copy_img

            def copy_clicked(code=booking["ticket_code"], b=copy_btn):
                self.copy_ticket_code(code, b)
            copy_btn.config(command=copy_clicked)
            copy_btn.pack(side=tk.LEFT, padx=(0, 10), ipadx=10, ipady=4)
            t.add_hover(copy_btn, t.CHIP_BG, t.CHIP_HOVER)

            if booking["can_cancel"]:
                def cancel_clicked(b=booking):
                    self.handle_cancel_booking(b)
                cancel_btn = tk.Button(btn_row, text="Cancel", bg="#e74c3c", fg="white", font=(t.FONT, 9, "bold"), relief="flat",
                                       command=cancel_clicked)
                x_img = ic.get_icon("close", size=13, color="#ffffff", master=btn_row)
                if x_img:
                    cancel_btn.config(image=x_img, compound=tk.LEFT)
                    cancel_btn.image = x_img
                cancel_btn.pack(side=tk.LEFT, ipadx=10, ipady=4)
                t.add_hover(cancel_btn, "#e74c3c", "#c0392b")

    def build_experiences_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        tk.Label(self.scrollable_frame, text="My Experiences", font=(t.FONT, 22, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 5))
        tk.Label(self.scrollable_frame, text="Tell us how it went. Your review helps other travellers to choose.", font=(t.FONT, 11), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 10))

        experiences = get_my_experiences(self.email)
        if not experiences:
            tk.Label(self.scrollable_frame, text="No past experiences yet. After you attend an event, it will appear here.", font=(t.FONT, 11, "italic"), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=10)
            return

        table = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
        table.pack(fill=tk.X, padx=30, pady=10)

        # column widths: name | date | time | location | review
        weights = [4, 3, 2, 3, 3]
        for col in range(len(weights)):
            table.columnconfigure(col, weight=weights[col], uniform="experience_cols")

        headings = ["Experience name", "Date", "Time", "Location", "Review"]
        for col in range(len(headings)):
            tk.Label(table, text=headings[col], font=(t.FONT, 10, "bold"), bg=t.CHIP_BG, fg=t.TEXT_MUTED,
                     anchor="w", padx=12, pady=8).grid(row=0, column=col, sticky="nsew")

        for i in range(len(experiences)):
            exp = experiences[i]
            grid_row = 1 + i * 2

            try:
                when = date.fromisoformat(exp["booking_date"]).strftime("%d %b %Y")
            except ValueError:
                when = exp["booking_date"]

            time_text = exp["event_time"]
            if not time_text:
                time_text = "TBA"
            venue = exp["venue_name"]
            if not venue:
                venue = "TBA"
            cells = [exp["event_title"], when, time_text, venue]
            for col in range(len(cells)):
                if col == 0:
                    weight = "bold"
                else:
                    weight = "normal"
                tk.Label(table, text=cells[col], font=(t.FONT, 10, weight), bg=t.CARD_BG, fg=t.TEXT,
                         anchor="w", justify="left", wraplength=220, padx=12, pady=10).grid(row=grid_row, column=col, sticky="nsew")

            def review_clicked(e=exp):
                self.open_review_window(e)

            rating = exp.get("review_rating")
            if rating is None:
                review_btn = tk.Button(table, text="Leave review", bg=t.PRIMARY, fg="white", font=(t.FONT, 9, "bold"), relief="flat",
                                       cursor="hand2", command=review_clicked)
                t.add_hover(review_btn, t.PRIMARY, t.PRIMARY_HOVER)
            else:
                review_btn = tk.Button(table, text=ic.emoji("star") + " " + format(float(rating), ".1f") + "  Edit", bg=t.CHIP_BG, fg=t.TEXT, font=(t.FONT, 9, "bold"),
                                       relief="flat", cursor="hand2", command=review_clicked)
                t.add_hover(review_btn, t.CHIP_BG, t.CHIP_HOVER)
            review_btn.grid(row=grid_row, column=4, sticky="w", padx=12, pady=8, ipadx=8, ipady=3)

            # thin line between the rows
            tk.Frame(table, bg=t.BORDER, height=1).grid(row=grid_row + 1, column=0, columnspan=5, sticky="ew")

    def open_review_window(self, exp):
        width = 420
        height = 440
        win = tk.Toplevel(self.root)
        win.title("Review your experience")
        win.configure(bg=t.CARD_BG)
        win.resizable(False, False)
        win.transient(self.root)

        # middle of the main window
        win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (height // 2)
        win.geometry(str(width) + "x" + str(height) + "+" + str(x) + "+" + str(y))
        try:
            win.grab_set()
        except tk.TclError:
            pass

        tk.Label(win, text="How was your experience?", font=(t.FONT, 15, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=25, pady=(20, 2))
        tk.Label(win, text=exp["event_title"], font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED, wraplength=370, justify="left").pack(anchor="w", padx=25)

        tk.Label(win, text="Your rating", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=25, pady=(18, 0))
        if exp.get("review_rating") is not None:
            start_rating = float(exp["review_rating"])
        else:
            start_rating = 0.0
        rating_var = tk.DoubleVar(value=start_rating)
        rating_label = tk.Label(win, text=format(start_rating, ".1f") + " / 5.0", font=(t.FONT, 16, "bold"), bg=t.CARD_BG, fg=t.ACCENT)
        rating_label.pack(anchor="w", padx=25)

        def on_slide(v):
            rating_label.config(text=format(float(v), ".1f") + " / 5.0")

        tk.Scale(win, from_=0, to=5, resolution=0.5, orient=tk.HORIZONTAL, length=370, tickinterval=1, showvalue=False,
                 variable=rating_var, bg=t.CARD_BG, fg=t.TEXT, troughcolor=t.BORDER, highlightthickness=0, font=(t.FONT, 9),
                 command=on_slide).pack(padx=25, pady=(0, 5))

        tk.Label(win, text="Your comment (optional)", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=25, pady=(10, 2))
        comment_box = tk.Text(win, height=6, width=44, font=(t.FONT, 10), wrap="word", relief="solid", bd=1)
        comment_box.pack(padx=25)
        old_comment = exp.get("review_comment")
        if not old_comment:
            old_comment = ""
        comment_box.insert("1.0", old_comment)

        counter = tk.Label(win, text="", font=(t.FONT, 8), bg=t.CARD_BG, fg=t.TEXT_MUTED)
        counter.pack(anchor="e", padx=25)

        # cuts the comment at 500 characters and shows how many there are
        def update_counter(event=None):
            text = comment_box.get("1.0", "end-1c")
            if len(text) > MAX_REVIEW_COMMENT:
                comment_box.delete("1.0", "end")
                comment_box.insert("1.0", text[:MAX_REVIEW_COMMENT])
                text = text[:MAX_REVIEW_COMMENT]
            counter.config(text=str(len(text)) + " / " + str(MAX_REVIEW_COMMENT))

        comment_box.bind("<KeyRelease>", update_counter)
        update_counter()

        def submit():
            result = submit_review(self.email, exp["id"], float(rating_var.get()), comment_box.get("1.0", "end").strip())
            if result.get("success"):
                win.destroy()
                messagebox.showinfo("Thank you", result.get("message", "Your review was saved."))
                self.build_experiences_content()
            else:
                messagebox.showerror("Cannot save review", result.get("message", "Something went wrong."), parent=win)

        btn_row = tk.Frame(win, bg=t.CARD_BG)
        btn_row.pack(fill=tk.X, padx=25, pady=15)

        cancel_btn = tk.Button(btn_row, text="Cancel", font=(t.FONT, 10, "bold"), bg=t.CHIP_BG, fg=t.TEXT, relief="flat", cursor="hand2", command=win.destroy)
        cancel_btn.pack(side=tk.LEFT, ipadx=15, ipady=6)
        t.add_hover(cancel_btn, t.CHIP_BG, t.CHIP_HOVER)

        submit_btn = tk.Button(btn_row, text="Submit review", font=(t.FONT, 10, "bold"), bg=t.PRIMARY, fg="white", relief="flat", cursor="hand2", command=submit)
        submit_btn.pack(side=tk.RIGHT, ipadx=15, ipady=6)
        t.add_hover(submit_btn, t.PRIMARY, t.PRIMARY_HOVER)

    def build_support_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        tk.Label(self.scrollable_frame, text="Support", font=(t.FONT, 22, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 5))

        form = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
        form.pack(fill=tk.X, padx=30, pady=10, ipady=10)

        # a ticket has to be about an event, one that is listed now or one the customer booked before
        all_titles = []
        for b in get_bookings_by_customer(self.email):
            all_titles.append(b["event_title"])
        for e in get_all_events():
            all_titles.append(e["title"])
        event_titles = []
        for title in all_titles:
            if title and title not in event_titles:
                event_titles.append(title)

        tk.Label(form, text="Event", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=(10, 2))
        event_var = tk.StringVar()
        event_box = ttk.Combobox(form, textvariable=event_var, values=event_titles, state="readonly", font=(t.FONT, 10))
        event_box.pack(fill=tk.X, padx=15)
        event_hint = tk.Label(form, text="Choose the event your message is about.", font=(t.FONT, 9), bg=t.CARD_BG, fg=t.ACCENT)
        event_hint.pack(anchor="w", padx=15, pady=(2, 0))

        tk.Label(form, text="Subject", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=(10, 2))
        subject_entry = tk.Entry(form, font=(t.FONT, 10))
        subject_entry.pack(fill=tk.X, padx=15)
        tk.Label(form, text="Message", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=(10, 2))
        message_box = tk.Text(form, height=5, font=(t.FONT, 10))
        message_box.pack(fill=tk.X, padx=15)

        def send():
            if not event_var.get():
                messagebox.showerror("Cannot send", "Please choose the event your message is about.")
                return
            result = create_support_ticket(self.email, subject_entry.get(), message_box.get("1.0", "end"), event_var.get())
            if result["success"]:
                messagebox.showinfo("Sent", result["message"])
                self.build_support_content()
            else:
                messagebox.showerror("Cannot send", result["message"])

        send_btn = tk.Button(form, text="Send message", font=(t.FONT, 10, "bold"), bg=t.PRIMARY, fg="white", relief="flat", command=send, state="disabled")
        send_btn.pack(anchor="w", padx=15, pady=(10, 5), ipadx=15, ipady=6)
        t.add_hover(send_btn, t.PRIMARY, t.PRIMARY_HOVER)

        # the send button only works after an event is picked
        def on_event_chosen(event=None):
            if event_var.get():
                send_btn.config(state="normal")
                event_hint.config(text="")
        event_box.bind("<<ComboboxSelected>>", on_event_chosen)
        if not event_titles:
            event_hint.config(text="There are no events to choose from yet, so a message cannot be sent.")

        # Old messages

        tickets = get_support_tickets_by_customer(self.email)
        if tickets:
            tk.Label(self.scrollable_frame, text="Your messages", font=(t.FONT, 14, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(15, 5))
        for ticket in tickets:
            card = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
            card.pack(fill=tk.X, padx=30, pady=6, ipady=6)
            if ticket["status"] == "Resolved":
                color = "#27ae60"
            else:
                color = t.ACCENT
            tk.Label(card, text=ticket['status'].upper() + "  |  " + str(ticket['created_at']), font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=color).pack(anchor="w", padx=15, pady=(6, 0))
            if ticket.get("event_title"):
                tk.Label(card, text="Event: " + str(ticket['event_title']), font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15)
            tk.Label(card, text=ticket["subject"], font=(t.FONT, 12, "bold"), bg=t.CARD_BG, fg=t.TEXT, wraplength=650, justify="left").pack(anchor="w", padx=15, pady=2)
            tk.Label(card, text=ticket["message"], font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED, wraplength=650, justify="left").pack(anchor="w", padx=15, pady=2)

    def copy_ticket_code(self, code, button):
        self.root.clipboard_clear()
        self.root.clipboard_append(code)
        button.config(text="Copied!")

    def handle_cancel_booking(self, booking):
        if not confirm_own_cancel(booking):
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
        modal.geometry("+" + str(x) + "+" + str(y))

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

    # category, max price and the search text
    def apply_all_filters(self):
        cat = self.current_filters["category"]
        max_p = self.current_filters["max_price"]
        query = self.search_query.lower()

        def parse_price(p_str):
            try:
                digits = ""
                for c in str(p_str):
                    if c.isdigit():
                        digits = digits + c
                if digits:
                    return int(digits)
                return 0
            except ValueError:
                return 0

        filtered = []
        for tour in self.all_tours:
            if cat != "All Experiences" and tour["category"] != cat:
                continue
            if parse_price(tour["price"]) > max_p:
                continue
            if query:
                desc = tour["desc"]
                if not desc:
                    desc = ""
                if not (query in tour["title"].lower() or query in tour["category"].lower() or query in desc.lower()):
                    continue
            filtered.append(tour)

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
