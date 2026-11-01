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

SEARCH_HINT = "Search tours and excursions..."


# the next date of the tour so we can show the seats that are left
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
            d = date.fromisoformat(dt[:10])
            return d
        except ValueError:
            pass
    return today


class PartnerWelcomeScreen(BaseWelcomeScreen):
    def __init__(self, root, email, tab="explore"):
        BaseWelcomeScreen.__init__(self, root, email, "OTA Partner")
        self.root = root
        self.search_query = ""
        self.active_category = "All Experiences"

        self.load_tours()

        # nav buttons
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
            category = e["category"]
            if not category:
                category = "General"
            venue_name = e.get("venue_name")
            if not venue_name:
                venue_name = "Unknown Venue"
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
                "level": e["is_recurring"],
                "rating": "5.0",
                "desc": e["desc"]
            })

    def _cart_button_label(self):
        count = get_cart_count(self.email)
        if count > 0:
            return "Shopping List (" + str(count) + ")"
        return "Shopping List"

    def refresh_cart_button(self):
        self.cart_btn.config(text=self._cart_button_label())

    def _clear_search_hint(self, event):
        if self.search_entry.get() == SEARCH_HINT:
            self.search_entry.delete(0, tk.END)

    # ====== Tab 1: Explore Tours ======
    def build_explore_content(self, filtered_tours=None):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.load_tours()
        if filtered_tours is not None:
            tours_to_show = filtered_tours
        else:
            tours_to_show = self.all_tours
        self.refresh_cart_button()

        banner = tk.Frame(self.scrollable_frame, bg=t.DARK_SOFT, padx=25, pady=15)
        banner.pack(fill=tk.X, padx=30, pady=(20, 10))

        globe_lbl = tk.Label(banner, text="OTA Partner Booking Portal", font=(t.FONT, 15, "bold"),
                             bg=t.DARK_SOFT, fg="white")
        globe_img = ic.get_icon("globe", size=18, color="#ffffff", master=banner)
        if globe_img:
            globe_lbl.config(image=globe_img, compound=tk.LEFT)
            globe_lbl.image = globe_img
        globe_lbl.pack(anchor="w")


        # Search bar
        search_frame = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        search_frame.pack(fill=tk.X, padx=30, pady=10)


        self.search_entry = tk.Entry(search_frame, font=(t.FONT, 11))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, ipady=5)
        if self.search_query:
            self.search_entry.insert(0, self.search_query)
        else:
            self.search_entry.insert(0, SEARCH_HINT)
        self.search_entry.bind("<FocusIn>", self._clear_search_hint)

        search_btn = tk.Button(search_frame, text="Search", bg=t.ACCENT, fg="white", font=(t.FONT, 10, "bold"),
                               relief="flat", command=self.apply_search)
        search_btn.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=3)
        t.add_hover(search_btn, t.ACCENT, "#e67e22")

        # category chips
        cat_frame = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        cat_frame.pack(fill=tk.X, padx=30, pady=5)

        unique_categories = []
        for tour in self.all_tours:
            if tour["category"] not in unique_categories:
                unique_categories.append(tour["category"])
        unique_categories.sort()
        categories = ["All Experiences"] + unique_categories

        for cat in categories:
            if self.active_category == cat:
                btn_bg = t.ACCENT
                btn_fg = "white"
                weight = "bold"
            else:
                btn_bg = t.CHIP_BG
                btn_fg = t.TEXT
                weight = "normal"

            def pick_category(c=cat):
                self.filter_by_category(c)
            tk.Button(cat_frame, text=cat, bg=btn_bg, fg=btn_fg, font=(t.FONT, 9, weight),
                      relief="flat", command=pick_category).pack(side=tk.LEFT, padx=4, ipady=4, ipadx=8)

        tk.Label(self.scrollable_frame, text="Available Experiences (" + str(len(tours_to_show)) + ")",
                 font=(t.FONT, 13, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(15, 5))

        if not tours_to_show:
            tk.Label(self.scrollable_frame, text="No events match your criteria.", font=(t.FONT, 10, "italic"),
                     bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=10)
            return

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

            star_lbl = tk.Label(top_row, text=ic.emoji("star") + " " + str(tour['rating']), font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.ACCENT)
            star_img = ic.get_icon("star", size=14, color=t.ACCENT, master=card)
            if star_img:
                star_lbl.config(image=star_img, compound=tk.LEFT)
                star_lbl.image = star_img
            star_lbl.pack(side=tk.LEFT)

            if isinstance(tour['price'], str):
                price_display = tour['price']
            else:
                price_display = str(tour['price']) + " AED"
            tk.Label(top_row, text="From " + price_display, font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.PRIMARY).pack(side=tk.RIGHT)

            tk.Label(card, text=tour["title"], font=(t.FONT, 13, "bold"), bg=t.CARD_BG, fg=t.TEXT,
                     wraplength=280, justify="left").pack(anchor="w", padx=15, pady=2)

            # venue and schedule
            sched_frame = tk.Frame(card, bg=t.CARD_BG)
            sched_frame.pack(anchor="w", padx=15, pady=1)
            pin_img = ic.get_icon("map_pin", size=12, color=t.TEXT_MUTED, master=card)
            if pin_img:
                lbl = tk.Label(sched_frame, image=pin_img, bg=t.CARD_BG)
                lbl.image = pin_img
                lbl.pack(side=tk.LEFT)
            tk.Label(sched_frame, text=str(tour['venue_name']), font=(t.FONT, 8), bg=t.CARD_BG, fg="#000000").pack(side=tk.LEFT)

            recur_img = ic.get_icon("repeat", size=12, color=t.TEXT_MUTED, master=card)
            if recur_img:
                lbl2 = tk.Label(sched_frame, image=recur_img, bg=t.CARD_BG)
                lbl2.image = recur_img
                lbl2.pack(side=tk.LEFT, padx=(6, 0))
            if tour['is_recurring'] == "One-Time":
                recur_text = "One-Time Event"
            else:
                recur_text = tour['is_recurring']
            if tour['is_recurring'] == "Recurring" and tour.get('recur_day') and tour['recur_day'] != "None":
                recur_text += " (" + str(tour['recur_day']) + ")"
            tk.Label(sched_frame, text="| " + str(recur_text), font=(t.FONT, 8), bg=t.CARD_BG, fg="#000000").pack(side=tk.LEFT)

            # seats left on the next date
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
            else:
                tk.Label(cap_box, text="Capacity:", font=(t.FONT, 8, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT, padx=(0, 4))
            CapacityBar(cap_box, remaining=remaining_val, total=cap_info['total'], width=90, height=12, bg=t.CARD_BG).pack(side=tk.LEFT)

            tk.Label(card, text=tour["desc"], font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED,
                     wraplength=280, justify="left").pack(anchor="w", padx=15, pady=6)

            btn_box = tk.Frame(card, bg=t.CARD_BG)
            btn_box.pack(anchor="w", padx=15, pady=(5, 15))

            def open_event(tr=tour):
                show_event_screen(self.root, self.email, tr, is_partner=True)

            details_btn = tk.Button(btn_box, text="Add to List", bg=t.PRIMARY, fg="white", font=(t.FONT, 10, "bold"),
                                    relief="flat", cursor="hand2", command=open_event)
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
        res = []
        q = self.search_query.lower()
        for tour in self.all_tours:
            if self.active_category != "All Experiences" and tour["category"] != self.active_category:
                continue
            if self.search_query:
                if not (q in tour["title"].lower() or q in tour["desc"].lower() or q in tour["venue_name"].lower()):
                    continue
            res.append(tour)
        self.build_explore_content(res)

    # ====== Tab 2: Shopping list (book many events and pay once) ======
    def build_shopping_list_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.refresh_cart_button()

        header_row = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        header_row.pack(anchor="w", padx=30, pady=(20, 5))
        cart_hdr_img = ic.get_icon("cart", size=20, color=t.TEXT, master=header_row)
        if cart_hdr_img:
            lbl = tk.Label(header_row, image=cart_hdr_img, bg=t.PAGE_BG)
            lbl.image = cart_hdr_img
            lbl.pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(header_row, text=ic.emoji("cart") + " OTA Partner Booking List", font=(t.FONT, 20, "bold"),
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

            exp_btn = tk.Button(empty_box, text="Browse Tours", font=(t.FONT, 10, "bold"), bg=t.PRIMARY,
                                fg="white", relief="flat", cursor="hand2", command=self.build_explore_content)
            exp_btn.pack(anchor="w", ipadx=15, ipady=6)
            t.add_hover(exp_btn, t.PRIMARY, t.PRIMARY_HOVER)
            return

        cart_container = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        cart_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        # totals
        total_guests = 0
        grand_total = 0
        for it in items:
            total_guests = total_guests + it["guests"]
            grand_total = grand_total + it["total_price"]

        summary_bar = tk.Frame(cart_container, bg=t.DARK, padx=20, pady=12)
        summary_bar.pack(fill=tk.X, pady=(0, 15))

        summary = ("Total Items: " + str(len(items)) + "  |  Total Guests: " + str(total_guests)
                   + "  |  Grand Total: " + str(grand_total) + " AED")
        tk.Label(summary_bar, text=summary,
                 font=(t.FONT, 12, "bold"), bg=t.DARK, fg="white").pack(side=tk.LEFT)

        def do_singular_payment():
            def on_payment_success(payment):
                res = checkout_cart(self.email)
                details = []
                if res["success"]:
                    # the bookings come back in the same order as the shopping list
                    bookings = res["bookings"]
                    n = len(bookings)
                    if len(items) < n:
                        n = len(items)
                    for i in range(n):
                        b = bookings[i]
                        it = items[i]
                        details.append({
                            "title": b["event_title"], "base": it["total_price"], "venue": b.get("venue_name"),
                            "date": b.get("booking_date"), "time": b.get("event_time"), "guests": b["guests"],
                            "client_name": b.get("client_name"),
                            "ticket_code": format_ticket_code(b["ticket_code"]),
                        })
                    after_close = self.build_bookings_content
                    error = None
                else:
                    for it in items:
                        details.append({
                            "title": it["title"], "base": it["total_price"], "venue": it.get("venue_name"),
                            "date": it["booking_date"], "guests": it["guests"], "client_name": it["client_name"],
                        })
                    after_close = self.build_shopping_list_content
                    error = res["message"]

                show_booking_details_window(self.root, details, payment, self.email,
                                            error=error, on_close=after_close)

            modal_items = []
            for it in items:
                modal_items.append({
                    "title": it["title"],
                    "date": it["booking_date"],
                    "guests": it["guests"],
                    "total": it["total_price"],
                    "client_name": it["client_name"]
                })

            show_demo_payment_modal(self.root, "OTA Partner Batch Payment (" + str(len(items)) + " Events)", modal_items, grand_total,
                                    on_payment_success, email=self.email)

        # total with vat = vat_breakdown(...)[2]
        with_vat = vat_breakdown(grand_total)[2]
        pay_all_btn = tk.Button(summary_bar, text="Pay All (" + format(with_vat, ",.2f") + " AED incl. VAT)",
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
            tk.Label(row1, text=str(it['total_price']) + " AED", font=(t.FONT, 13, "bold"), bg=t.CARD_BG, fg=t.PRIMARY).pack(side=tk.RIGHT)

            row2 = tk.Frame(card, bg=t.CARD_BG)
            row2.pack(fill=tk.X, padx=15, pady=2)

            if it['client_name']:
                group_str = "Client/Group: " + str(it['client_name'])
            else:
                group_str = "Group: Standard Booking"

            # date, guests and price with the icons
            cal_lbl = tk.Label(row2, bg=t.CARD_BG)
            cal_img = ic.get_icon("calendar", size=12, color=t.TEXT_MUTED, master=card)
            if cal_img:
                cal_lbl.config(image=cal_img)
                cal_lbl.image = cal_img
            cal_lbl.pack(side=tk.LEFT)
            tk.Label(row2, text=str(it['booking_date']) + " | ", font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT)

            users_lbl = tk.Label(row2, bg=t.CARD_BG)
            u_img = ic.get_icon("users", size=12, color=t.TEXT_MUTED, master=card)
            if u_img:
                users_lbl.config(image=u_img)
                users_lbl.image = u_img
            users_lbl.pack(side=tk.LEFT)
            tk.Label(row2, text=str(it['guests']) + " guests ", font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT)

            tk.Label(row2, text=str(it['unit_price']) + " AED/guest  |  " + group_str, font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT)

            def remove_clicked(item_id=it["id"]):
                self.handle_remove_cart_item(item_id)

            remove_btn = tk.Button(row2, text=ic.emoji("close") + " Remove", font=(t.FONT, 9), bg=t.CHIP_BG, fg="#e74c3c",
                                   relief="flat", cursor="hand2", command=remove_clicked)
            x_img = ic.get_icon("close", size=12, color="#e74c3c", master=row2)
            if x_img:
                remove_btn.config(image=x_img, compound=tk.LEFT)
                remove_btn.image = x_img
            remove_btn.pack(side=tk.RIGHT, padx=(10, 0), ipadx=6)
            t.add_hover(remove_btn, t.CHIP_BG, "#fcdbd9")

        clear_btn = tk.Button(cart_container, text=ic.emoji("close") + " Clear Entire List", font=(t.FONT, 9), bg=t.CHIP_BG,
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

    # ====== Tab 3: Partner Bookings ======
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
        tk.Label(header_row, text="Partner Bookings", font=(t.FONT, 20, "bold"),
                 bg=t.PAGE_BG, fg=t.TEXT).pack(side=tk.LEFT)
        refresh_btn = tk.Button(header_row, text="Refresh", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT,
                                relief="solid", bd=1, cursor="hand2", command=self.build_bookings_content)
        refresh_btn.pack(side=tk.RIGHT, ipadx=10, ipady=3)
        t.add_hover(refresh_btn, t.CARD_BG, t.CHIP_HOVER)

        bookings = get_bookings_by_customer(self.email)
        if not bookings:
            tk.Label(self.scrollable_frame, text="You have no bookings yet.", font=(t.FONT, 11, "italic"),
                     bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=10)
            exp_btn = tk.Button(self.scrollable_frame, text="Explore Tours", font=(t.FONT, 10, "bold"),
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
            tk.Label(top_row, text=str(b['total_price']) + " AED", font=(t.FONT, 11, "bold"),
                     bg=t.CARD_BG, fg=t.ACCENT).pack(side=tk.RIGHT)

            title_row = tk.Frame(card, bg=t.CARD_BG)
            title_row.pack(fill=tk.X, padx=15, pady=2)
            tk.Label(title_row, text=b["event_title"], font=(t.FONT, 13, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(side=tk.LEFT)
            if b.get("client_name"):
                tk.Label(title_row, text="[" + str(b['client_name']) + "]", font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.PRIMARY).pack(side=tk.LEFT, padx=8)

            try:
                when = date.fromisoformat(b["booking_date"]).strftime("%A, %d %b %Y")
            except ValueError:
                when = b["booking_date"]

            time_text = b['event_time']
            if not time_text:
                time_text = 'TBA'
            venue = b['venue_name']
            if not venue:
                venue = 'Venue TBA'
            info_row = tk.Frame(card, bg=t.CARD_BG)
            info_row.pack(anchor="w", padx=15, pady=2)
            tk.Label(info_row, text=str(when) + " at " + str(time_text) + " | " + str(venue),
                     font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT)
            u_img2 = ic.get_icon("users", size=12, color=t.TEXT_MUTED, master=card)
            if u_img2:
                ul2 = tk.Label(info_row, image=u_img2, bg=t.CARD_BG)
                ul2.image = u_img2
                ul2.pack(side=tk.LEFT, padx=(8, 2))
            tk.Label(info_row, text=str(b['guests']) + " guest(s) (OTA Extended)", font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT)

            tk.Label(card, text="TICKET CODE (GIVE TO CUSTOMER)", font=(t.FONT, 8, "bold"),
                     bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=(8, 0))
            if b["status"] == "Confirmed":
                code_color = t.TEXT
            else:
                code_color = t.TEXT_MUTED
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

            copy_btn = tk.Button(btn_row, text="Copy Ticket Code", bg=t.CHIP_BG, fg=t.TEXT, font=(t.FONT, 9, "bold"), relief="flat")
            copy_img = ic.get_icon("copy", size=13, color=t.TEXT, master=btn_row)
            if copy_img:
                copy_btn.config(image=copy_img, compound=tk.LEFT)
                copy_btn.image = copy_img

            def copy_clicked(code=b["ticket_code"], btn=copy_btn):
                self.copy_code(code, btn)
            copy_btn.config(command=copy_clicked)
            copy_btn.pack(side=tk.LEFT, padx=(0, 10), ipadx=10, ipady=4)
            t.add_hover(copy_btn, t.CHIP_BG, t.CHIP_HOVER)

            if b["can_cancel"]:
                def cancel_clicked(bk=b):
                    self.handle_cancel(bk)
                cancel_btn = tk.Button(btn_row, text=ic.emoji("close") + " Cancel Booking", bg="#e74c3c", fg="white", font=(t.FONT, 9, "bold"), relief="flat",
                                       command=cancel_clicked)
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
        button.config(text=ic.emoji("check") + " Copied!")

        # put the old text back after 1.5 seconds
        def put_back():
            button.config(text=orig_text)
        self.root.after(1500, put_back)

    def handle_cancel(self, booking):
        if not confirm_own_cancel(booking):
            return
        res = cancel_booking(booking["id"], self.email)
        if res["success"]:
            messagebox.showinfo("Cancelled", res['message'] + "\n\nThe seats have been released.")
        else:
            messagebox.showerror("Error", res["message"])
        self.build_bookings_content()


def show_partner_welcome(root, email, tab="explore"):
    PartnerWelcomeScreen(root, email, tab=tab)
