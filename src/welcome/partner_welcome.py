from datetime import date, timedelta
import tkinter as tk
from tkinter import messagebox
from .users_welcome import BaseWelcomeScreen
from .cancellation import policy_line, cancelled_line, confirm_own_cancel
from screens.event_screen import show_event_screen
from database import (
    get_all_events, get_bookings_by_customer, cancel_booking, format_ticket_code,
    get_event_capacity, get_cart_items, get_cart_count, remove_from_cart,
    clear_cart, checkout_cart
)
from capacity_bar import CapacityBar
from payment import show_demo_payment_modal, show_booking_details_window
from pricing import vat_breakdown
import theme as t
import icons as ic
import event_images


def _next_date_for_tour(tour):
    """Finds the upcoming date for this tour to get live remaining capacity."""
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
            d = date.fromisoformat((tour.get("event_datetime") or "")[:10])
            return d
        except ValueError:
            pass
    return today


class PartnerWelcomeScreen(BaseWelcomeScreen):
    def __init__(self, root, email, tab="explore"):
        super().__init__(root, email, "OTA Partner")
        self.root = root
        self.search_query = ""
        self.active_category = "All Experiences"

        self.load_tours()

        # Nav bar items (No Partner Terms page)
        self.explore_btn = self.add_nav_button("Explore Tours", self.build_explore_content, icon="compass")
        self.cart_btn = self.add_nav_button(self._cart_button_label(), self.build_shopping_list_content)
        self.bookings_btn = self.add_nav_button("Partner Bookings", self.build_bookings_content, icon="handshake")

        if tab == "cart":
            self.build_shopping_list_content()
        elif tab == "bookings":
            self.build_bookings_content()
        else:
            self.build_explore_content()

    def load_tours(self):
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

    def _cart_button_label(self):
        count = get_cart_count(self.email)
        return f"Shopping List ({count})" if count > 0 else f"Shopping List"

    def refresh_cart_button(self):
        self.cart_btn.config(text=self._cart_button_label())

    # ==============================================================
    # TAB 1: Explore Tours (Partner View with Dynamic Capacity)
    # ==============================================================
    def build_explore_content(self, filtered_tours=None):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.load_tours()
        tours_to_show = filtered_tours if filtered_tours is not None else self.all_tours
        self.refresh_cart_button()

        # Banner
        banner = tk.Frame(self.scrollable_frame, bg=t.DARK_SOFT, padx=25, pady=15)
        banner.pack(fill=tk.X, padx=30, pady=(20, 10))

        globe_lbl = tk.Label(banner, text="OTA Partner Booking Portal", font=(t.FONT, 15, "bold"),
                             bg=t.DARK_SOFT, fg="white")
        globe_img = ic.get_icon("globe", size=18, color="#ffffff", master=banner)
        if globe_img:
            globe_lbl.config(image=globe_img, compound=tk.LEFT)
            globe_lbl.image = globe_img
        globe_lbl.pack(anchor="w")


        # Search Bar
        search_frame = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        search_frame.pack(fill=tk.X, padx=30, pady=10)


        self.search_entry = tk.Entry(search_frame, font=(t.FONT, 11))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, ipady=5)
        self.search_entry.insert(0, self.search_query or "Search tours and excursions...")
        self.search_entry.bind("<FocusIn>", lambda e: self.search_entry.delete(0, tk.END) if self.search_entry.get() == "Search tours and excursions..." else None)

        search_btn = tk.Button(search_frame, text="Search", bg=t.ACCENT, fg="white", font=(t.FONT, 10, "bold"),
                               relief="flat", command=self.apply_search)
        search_btn.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=3)
        t.add_hover(search_btn, t.ACCENT, "#e67e22")

        # Category Chips
        cat_frame = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        cat_frame.pack(fill=tk.X, padx=30, pady=5)

        unique_categories = sorted(list(set(tour["category"] for tour in self.all_tours)))
        categories = ["All Experiences"] + unique_categories

        for cat in categories:
            is_active = self.active_category == cat
            btn_bg = t.ACCENT if is_active else t.CHIP_BG
            btn_fg = "white" if is_active else t.TEXT
            tk.Button(cat_frame, text=cat, bg=btn_bg, fg=btn_fg, font=(t.FONT, 9, "bold" if is_active else "normal"),
                      relief="flat", command=lambda c=cat: self.filter_by_category(c)).pack(side=tk.LEFT, padx=4, ipady=4, ipadx=8)

        tk.Label(self.scrollable_frame, text=f"Available Experiences ({len(tours_to_show)})",
                 font=(t.FONT, 13, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(15, 5))

        if not tours_to_show:
            tk.Label(self.scrollable_frame, text="No events match your criteria.", font=(t.FONT, 10, "italic"),
                     bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=10)
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

            star_lbl = tk.Label(top_row, text=f"{ic.emoji('star')} {tour['rating']}", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.ACCENT)
            star_img = ic.get_icon("star", size=14, color=t.ACCENT, master=card)
            if star_img:
                star_lbl.config(image=star_img, compound=tk.LEFT)
                star_lbl.image = star_img
            star_lbl.pack(side=tk.LEFT)

            price_display = tour['price'] if isinstance(tour['price'], str) else f"{tour['price']} AED"
            tk.Label(top_row, text=f"From {price_display}", font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.PRIMARY).pack(side=tk.RIGHT)

            tk.Label(card, text=tour["title"], font=(t.FONT, 13, "bold"), bg=t.CARD_BG, fg=t.TEXT,
                     wraplength=280, justify="left").pack(anchor="w", padx=15, pady=2)

            # Schedule info
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
            if tour['is_recurring'] == "Recurring" and tour.get('recur_day') and tour['recur_day'] != "None":
                recur_text += f" ({tour['recur_day']})"
            tk.Label(sched_frame, text=f"| {recur_text}", font=(t.FONT, 8), bg=t.CARD_BG, fg="#000000").pack(side=tk.LEFT)

            # Live dynamic capacity for the upcoming occurrence
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
            else:
                tk.Label(cap_box, text=f"Capacity:", font=(t.FONT, 8, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT, padx=(0, 4))
            CapacityBar(cap_box, remaining=remaining_val, total=cap_info['total'], width=90, height=12, bg=t.CARD_BG).pack(side=tk.LEFT)

            tk.Label(card, text=tour["desc"], font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED,
                     wraplength=280, justify="left").pack(anchor="w", padx=15, pady=6)

            btn_box = tk.Frame(card, bg=t.CARD_BG)
            btn_box.pack(anchor="w", padx=15, pady=(5, 15))

            details_btn = tk.Button(btn_box, text=f"Add to List", bg=t.PRIMARY, fg="white", font=(t.FONT, 10, "bold"),
                                    relief="flat", cursor="hand2", command=lambda tr=tour: show_event_screen(self.root, self.email, tr, is_partner=True))
            cart_img = ic.get_icon("cart", size=14, color="#ffffff", master=btn_box)
            if cart_img:
                details_btn.config(image=cart_img, compound=tk.LEFT)
                details_btn.image = cart_img
            details_btn.pack(side=tk.LEFT, ipadx=10, ipady=5)
            t.add_hover(details_btn, t.PRIMARY, t.PRIMARY_HOVER)

    def apply_search(self):
        query = self.search_entry.get().strip()
        if query.lower() == "search tours and excursions...":
            query = ""
        self.search_query = query
        self._filter_and_show()

    def filter_by_category(self, category):
        self.active_category = category
        self._filter_and_show()

    def _filter_and_show(self):
        res = self.all_tours
        if self.active_category != "All Experiences":
            res = [tour for tour in res if tour["category"] == self.active_category]
        if self.search_query:
            q = self.search_query.lower()
            res = [tour for tour in res if q in tour["title"].lower() or q in tour["desc"].lower() or q in tour["venue_name"].lower()]
        self.build_explore_content(res)

    # ==============================================================
    # TAB 2: Shopping List (Multi-event batch booking with singular payment)
    # ==============================================================
    def build_shopping_list_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.refresh_cart_button()

        # Header with cart icon
        header_row = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        header_row.pack(anchor="w", padx=30, pady=(20, 5))
        cart_hdr_img = ic.get_icon("cart", size=20, color=t.TEXT, master=header_row)
        if cart_hdr_img:
            lbl = tk.Label(header_row, image=cart_hdr_img, bg=t.PAGE_BG)
            lbl.image = cart_hdr_img
            lbl.pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(header_row, text=f"{ic.emoji('cart')} OTA Partner Booking List", font=(t.FONT, 20, "bold"),
                 bg=t.PAGE_BG, fg=t.TEXT).pack(side=tk.LEFT)



        items = get_cart_items(self.email)

        if not items:
            empty_box = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid",
                                 highlightbackground=t.BORDER, padx=30, pady=30)
            empty_box.pack(fill=tk.X, padx=30, pady=10)
            tk.Label(empty_box, text="Your shopping list is currently empty.", font=(t.FONT, 12, "bold"),
                     bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w")
            tk.Label(empty_box, text="Browse available excursions and add them to your list with your custom client groups.",
                     font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(5, 15))

            exp_btn = tk.Button(empty_box, text=f"Browse Tours", font=(t.FONT, 10, "bold"), bg=t.PRIMARY,
                                fg="white", relief="flat", cursor="hand2", command=self.build_explore_content)
            exp_btn.pack(anchor="w", ipadx=15, ipady=6)
            t.add_hover(exp_btn, t.PRIMARY, t.PRIMARY_HOVER)
            return

        cart_container = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        cart_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        total_guests = sum(it["guests"] for it in items)
        grand_total = sum(it["total_price"] for it in items)

        summary_bar = tk.Frame(cart_container, bg=t.DARK, padx=20, pady=12)
        summary_bar.pack(fill=tk.X, pady=(0, 15))

        tk.Label(summary_bar, text=f"Total Items: {len(items)}  |  Total Guests: {total_guests}  |  Grand Total: {grand_total} AED",
                 font=(t.FONT, 12, "bold"), bg=t.DARK, fg="white").pack(side=tk.LEFT)

        def do_singular_payment():
            def on_payment_success(payment):
                res = checkout_cart(self.email)
                if res["success"]:
                    # Bookings come back in the same order as the shopping list.
                    details = [{
                        "title": b["event_title"], "base": it["total_price"], "venue": b.get("venue_name"),
                        "date": b.get("booking_date"), "time": b.get("event_time"), "guests": b["guests"],
                        "client_name": b.get("client_name"),
                        "ticket_code": format_ticket_code(b["ticket_code"]),
                    } for b, it in zip(res["bookings"], items)]
                    after_close = self.build_bookings_content
                else:
                    details = [{
                        "title": it["title"], "base": it["total_price"], "venue": it.get("venue_name"),
                        "date": it["booking_date"], "guests": it["guests"], "client_name": it["client_name"],
                    } for it in items]
                    after_close = self.build_shopping_list_content

                show_booking_details_window(self.root, details, payment, self.email,
                                            error=None if res["success"] else res["message"], on_close=after_close)

            modal_items = [{
                "title": it["title"],
                "date": it["booking_date"],
                "guests": it["guests"],
                "total": it["total_price"],
                "client_name": it["client_name"]
            } for it in items]

            show_demo_payment_modal(self.root, f"OTA Partner Batch Payment ({len(items)} Events)", modal_items, grand_total,
                                    on_payment_success, email=self.email)

        pay_all_btn = tk.Button(summary_bar, text=f"Pay All ({vat_breakdown(grand_total)[2]:,.2f} AED incl. VAT)",
                                font=(t.FONT, 11, "bold"), bg=t.ACCENT, fg="white", relief="flat",
                                cursor="hand2", command=do_singular_payment)
        payment_img = ic.get_icon("payment", size=16, color="#ffffff", master=summary_bar)
        if payment_img:
            pay_all_btn.config(image=payment_img, compound=tk.LEFT)
            pay_all_btn.image = payment_img
        pay_all_btn.pack(side=tk.RIGHT, ipadx=12, ipady=4)
        t.add_hover(pay_all_btn, t.ACCENT, "#e67e22")

        for it in items:
            card = tk.Frame(cart_container, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
            card.pack(fill=tk.X, pady=6, ipady=8)

            row1 = tk.Frame(card, bg=t.CARD_BG)
            row1.pack(fill=tk.X, padx=15, pady=(8, 2))

            tk.Label(row1, text=it["title"], font=(t.FONT, 13, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(side=tk.LEFT)
            tk.Label(row1, text=f"{it['total_price']} AED", font=(t.FONT, 13, "bold"), bg=t.CARD_BG, fg=t.PRIMARY).pack(side=tk.RIGHT)

            row2 = tk.Frame(card, bg=t.CARD_BG)
            row2.pack(fill=tk.X, padx=15, pady=2)

            group_str = f"Client/Group: {it['client_name']}" if it['client_name'] else "Group: Standard Booking"

            # Row2 info with icons
            cal_lbl = tk.Label(row2, bg=t.CARD_BG)
            cal_img = ic.get_icon("calendar", size=12, color=t.TEXT_MUTED, master=card)
            if cal_img:
                cal_lbl.config(image=cal_img)
                cal_lbl.image = cal_img
            cal_lbl.pack(side=tk.LEFT)
            tk.Label(row2, text=f"{it['booking_date']} | ", font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT)

            users_lbl = tk.Label(row2, bg=t.CARD_BG)
            u_img = ic.get_icon("users", size=12, color=t.TEXT_MUTED, master=card)
            if u_img:
                users_lbl.config(image=u_img)
                users_lbl.image = u_img
            users_lbl.pack(side=tk.LEFT)
            tk.Label(row2, text=f"{it['guests']} guests ", font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT)

            tk.Label(row2, text=f"{it['unit_price']} AED/guest  |  {group_str}", font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT)

            def make_remove_cmd(item_id):
                return lambda: self.handle_remove_cart_item(item_id)

            remove_btn = tk.Button(row2, text=f"{ic.emoji('close')} Remove", font=(t.FONT, 9), bg=t.CHIP_BG, fg="#e74c3c",
                                   relief="flat", cursor="hand2", command=make_remove_cmd(it["id"]))
            x_img = ic.get_icon("close", size=12, color="#e74c3c", master=row2)
            if x_img:
                remove_btn.config(image=x_img, compound=tk.LEFT)
                remove_btn.image = x_img
            remove_btn.pack(side=tk.RIGHT, padx=(10, 0), ipadx=6)
            t.add_hover(remove_btn, t.CHIP_BG, "#fcdbd9")

        clear_btn = tk.Button(cart_container, text=f"{ic.emoji('close')} Clear Entire List", font=(t.FONT, 9), bg=t.CHIP_BG,
                              fg="#e74c3c", relief="flat", cursor="hand2", command=self.handle_clear_cart)
        trash_img = ic.get_icon("trash", size=13, color=t.TEXT_MUTED, master=cart_container)
        if trash_img:
            clear_btn.config(image=trash_img, compound=tk.LEFT)
            clear_btn.image = trash_img
        clear_btn.pack(anchor="w", pady=(10, 0), ipadx=8, ipady=3)
        t.add_hover(clear_btn, t.CHIP_BG, t.CHIP_HOVER)

    def handle_remove_cart_item(self, cart_id):
        remove_from_cart(cart_id, self.email)
        self.build_shopping_list_content()

    def handle_clear_cart(self):
        if messagebox.askyesno("Clear List", "Are you sure you want to remove all items from your shopping list?"):
            clear_cart(self.email)
            self.build_shopping_list_content()

    # ==============================================================
    # TAB 3: Partner Bookings (Confirmed OTA Tickets)
    # ==============================================================
    def build_bookings_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.refresh_cart_button()

        header_row = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        header_row.pack(fill=tk.X, padx=30, pady=(20, 5))
        list_img = ic.get_icon("list", size=20, color=t.TEXT, master=header_row)
        if list_img:
            lbl = tk.Label(header_row, image=list_img, bg=t.PAGE_BG)
            lbl.image = list_img
            lbl.pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(header_row, text=f"Partner Bookings", font=(t.FONT, 20, "bold"),
                 bg=t.PAGE_BG, fg=t.TEXT).pack(side=tk.LEFT)
        refresh_btn = tk.Button(header_row, text="Refresh", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT,
                                relief="solid", bd=1, cursor="hand2", command=self.build_bookings_content)
        refresh_btn.pack(side=tk.RIGHT, ipadx=10, ipady=3)
        t.add_hover(refresh_btn, t.CARD_BG, t.CHIP_HOVER)

        bookings = get_bookings_by_customer(self.email)
        if not bookings:
            tk.Label(self.scrollable_frame, text="You have no bookings yet.", font=(t.FONT, 11, "italic"),
                     bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=10)
            exp_btn = tk.Button(self.scrollable_frame, text=f"Explore Tours", font=(t.FONT, 10, "bold"),
                                bg=t.PRIMARY, fg="white", relief="flat", command=self.build_explore_content)
            exp_btn.pack(anchor="w", padx=30, ipadx=15, ipady=6)
            t.add_hover(exp_btn, t.PRIMARY, t.PRIMARY_HOVER)
            return

        status_colors = {"Confirmed": "#27ae60", "Checked in": t.PRIMARY, "Expired": t.TEXT_MUTED, "Cancelled": "#e74c3c"}

        for b in bookings:
            card = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
            card.pack(fill=tk.X, padx=30, pady=10, ipady=10)

            top_row = tk.Frame(card, bg=t.CARD_BG)
            top_row.pack(fill=tk.X, padx=15, pady=(5, 0))
            tk.Label(top_row, text=b["status"].upper(), font=(t.FONT, 9, "bold"),
                     bg=t.CARD_BG, fg=status_colors.get(b["status"], t.TEXT_MUTED)).pack(side=tk.LEFT)
            tk.Label(top_row, text=f"{b['total_price']} AED", font=(t.FONT, 11, "bold"),
                     bg=t.CARD_BG, fg=t.ACCENT).pack(side=tk.RIGHT)

            title_row = tk.Frame(card, bg=t.CARD_BG)
            title_row.pack(fill=tk.X, padx=15, pady=2)
            tk.Label(title_row, text=b["event_title"], font=(t.FONT, 13, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(side=tk.LEFT)
            if b.get("client_name"):
                tk.Label(title_row, text=f"[{b['client_name']}]", font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.PRIMARY).pack(side=tk.LEFT, padx=8)

            try:
                when = date.fromisoformat(b["booking_date"]).strftime("%A, %d %b %Y")
            except ValueError:
                when = b["booking_date"]

            info_row = tk.Frame(card, bg=t.CARD_BG)
            info_row.pack(anchor="w", padx=15, pady=2)
            tk.Label(info_row, text=f"{when} at {b['event_time'] or 'TBA'} | {b['venue_name'] or 'Venue TBA'}",
                     font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT)
            u_img2 = ic.get_icon("users", size=12, color=t.TEXT_MUTED, master=card)
            if u_img2:
                ul2 = tk.Label(info_row, image=u_img2, bg=t.CARD_BG)
                ul2.image = u_img2
                ul2.pack(side=tk.LEFT, padx=(8, 2))
            tk.Label(info_row, text=f"{b['guests']} guest(s) (OTA Extended)", font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT)

            tk.Label(card, text=f"TICKET CODE (GIVE TO CUSTOMER)", font=(t.FONT, 8, "bold"),
                     bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=(8, 0))
            code_color = t.TEXT if b["status"] == "Confirmed" else t.TEXT_MUTED
            tk.Label(card, text=format_ticket_code(b["ticket_code"]), font=("Consolas", 15, "bold"),
                     bg=t.CARD_BG, fg=code_color).pack(anchor="w", padx=15, pady=(0, 5))
            if b["status"] == "Cancelled":
                tk.Label(card, text=cancelled_line(b, self.email), font=(t.FONT, 9), bg=t.CARD_BG, fg="#c0392b",
                         wraplength=600, justify="left").pack(anchor="w", padx=15, pady=(0, 4))
            elif b["status"] == "Confirmed":
                tk.Label(card, text=policy_line(b), font=(t.FONT, 9, "italic"), bg=t.CARD_BG,
                         fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=(0, 4))

            btn_row = tk.Frame(card, bg=t.CARD_BG)
            btn_row.pack(anchor="w", padx=15, pady=(5, 5))

            copy_btn = tk.Button(btn_row, text=f"Copy Ticket Code", bg=t.CHIP_BG, fg=t.TEXT, font=(t.FONT, 9, "bold"), relief="flat")
            copy_img = ic.get_icon("copy", size=13, color=t.TEXT, master=btn_row)
            if copy_img:
                copy_btn.config(image=copy_img, compound=tk.LEFT)
                copy_btn.image = copy_img
            copy_btn.config(command=lambda code=b["ticket_code"], btn=copy_btn: self.copy_code(code, btn))
            copy_btn.pack(side=tk.LEFT, padx=(0, 10), ipadx=10, ipady=4)
            t.add_hover(copy_btn, t.CHIP_BG, t.CHIP_HOVER)

            if b["can_cancel"]:
                cancel_btn = tk.Button(btn_row, text=f"{ic.emoji('close')} Cancel Booking", bg="#e74c3c", fg="white", font=(t.FONT, 9, "bold"), relief="flat",
                                       command=lambda bk=b: self.handle_cancel(bk))
                x_img = ic.get_icon("close", size=13, color="#ffffff", master=btn_row)
                if x_img:
                    cancel_btn.config(image=x_img, compound=tk.LEFT)
                    cancel_btn.image = x_img
                cancel_btn.pack(side=tk.LEFT, ipadx=10, ipady=4)
                t.add_hover(cancel_btn, "#e74c3c", "#c0392b")

    def copy_code(self, code, button):
        self.root.clipboard_clear()
        self.root.clipboard_append(code)
        orig_text = button.cget("text")
        button.config(text=f"{ic.emoji('check')} Copied!")
        self.root.after(1500, lambda: button.config(text=orig_text))

    def handle_cancel(self, booking):
        if not confirm_own_cancel(booking):
            return
        res = cancel_booking(booking["id"], self.email)
        if res["success"]:
            messagebox.showinfo("Cancelled", f"{res['message']}\n\nThe seats have been released.")
        else:
            messagebox.showerror("Error", res["message"])
        self.build_bookings_content()


def show_partner_welcome(root, email, tab="explore"):
    PartnerWelcomeScreen(root, email, tab=tab)
