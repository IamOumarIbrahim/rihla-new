import calendar
from datetime import date
import tkinter as tk
from tkinter import messagebox
import navigate
import theme as t
from ui import clear_window
from database import (
    create_booking, format_ticket_code, price_to_int,
    get_event_capacity, MAX_GUESTS_PER_BOOKING, add_to_cart
)
from capacity_bar import CapacityBar
from payment import show_demo_payment_modal
import icons as ic


def show_event_screen(root, email, tour, is_partner=False):
    clear_window(root)
    # Read capacity fresh from the database, because vehicles can change after the list was loaded.
    capacity = get_event_capacity(tour["id"])

    container = tk.Frame(root, bg=t.CARD_BG)
    container.pack(fill=tk.BOTH, expand=True)
    container.rowconfigure(0, weight=1)
    container.columnconfigure(0, weight=7, uniform="cols")
    container.columnconfigure(1, weight=3, uniform="cols")

    # ----- Left Side: Event Details -----
    left_frame = tk.Frame(container, bg=t.CARD_BG, padx=40, pady=30)
    left_frame.grid(row=0, column=0, sticky="nsew")

    def go_back():
        if is_partner:
            from welcome.partner_welcome import show_partner_welcome
            show_partner_welcome(root, email, tab="explore")
        else:
            navigate.show_welcome(root, email)

    back_btn = tk.Button(left_frame, text=" Back", font=(t.FONT, 10), bg=t.CARD_BG, fg=t.PRIMARY,
                         bd=0, relief="flat", cursor="hand2", command=go_back)
    back_img = ic.get_icon("back", size=14, color=t.PRIMARY, master=left_frame)
    if back_img:
        back_btn.config(image=back_img, compound=tk.LEFT)
        back_btn.image = back_img
    back_btn.pack(anchor="w", pady=(0, 15))

    tk.Label(left_frame, text=tour["title"], font=(t.FONT, 22, "bold"), bg=t.CARD_BG, fg=t.TEXT,
             wraplength=600, justify="left").pack(anchor="w", pady=5)

    meta_row = tk.Frame(left_frame, bg=t.CARD_BG)
    meta_row.pack(anchor="w", pady=5)

    star_lbl = tk.Label(meta_row, text=f" {tour['rating']}", font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.ACCENT)
    star_img = ic.get_icon("star", size=14, color=t.ACCENT, master=left_frame)
    if star_img:
        star_lbl.config(image=star_img, compound=tk.LEFT)
        star_lbl.image = star_img
    star_lbl.pack(side=tk.LEFT, padx=(0, 15))
    tk.Label(meta_row, text=f"Category: {tour['category']}", font=(t.FONT, 11), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT)

    tk.Label(left_frame, text="Overview", font=(t.FONT, 14, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", pady=(20, 5))
    tk.Label(left_frame, text=tour["desc"], font=(t.FONT, 11), bg=t.CARD_BG, fg=t.TEXT_MUTED,
             wraplength=600, justify="left").pack(anchor="w", pady=5)

    tk.Label(left_frame, text="Event Details", font=(t.FONT, 14, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", pady=(20, 5))
    recurrence_text = tour.get("is_recurring") or "One-Time"
    if recurrence_text == "Recurring" and tour.get("recur_day") not in (None, "", "None", "N/A"):
        recurrence_text += f" ({tour['recur_day']})"

    # Detail rows with icons
    details_data = [
        ("map_pin", f"Venue: {tour.get('venue_name') or 'To be announced'}"),
        ("calendar", f"Date and time: {tour.get('event_datetime') or 'To be announced'}"),
        ("repeat",   f"Type: {recurrence_text}"),
    ]
    for icon_key, detail_text in details_data:
        row = tk.Frame(left_frame, bg=t.CARD_BG)
        row.pack(anchor="w", pady=2)
        dimg = ic.get_icon(icon_key, size=13, color=t.TEXT_MUTED, master=left_frame)
        if dimg:
            lbl = tk.Label(row, image=dimg, bg=t.CARD_BG)
            lbl.image = dimg
            lbl.pack(side=tk.LEFT, padx=(0, 6))
        tk.Label(row, text=detail_text, font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT)

    tk.Label(left_frame, text="Capacity and Vehicles", font=(t.FONT, 14, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", pady=(20, 5))

    left_cap_bar = CapacityBar(left_frame, remaining=capacity["total"], total=capacity["total"], width=140, height=14, bg=t.CARD_BG)
    left_cap_bar.pack(anchor="w", pady=(2, 6))

    capacity_lines = [f"Total Capacity: {capacity['total']} guests per date"]
    if capacity["vehicles"]:
        for vehicle in capacity["vehicles"]:
            capacity_lines.append(f"Vehicles: {vehicle['count']} x {vehicle['vehicle_type']} ({vehicle['seats_each']} seats each)")
        capacity_lines.append("The seats of these vehicles set the limit for this event.")
    else:
        capacity_lines.append("Vehicles: none assigned to this event")

    for item in capacity_lines:
        row = tk.Frame(left_frame, bg=t.CARD_BG)
        row.pack(anchor="w", pady=2)
        truck_img = ic.get_icon("truck", size=13, color=t.TEXT_MUTED, master=left_frame)
        if truck_img:
            lbl = tk.Label(row, image=truck_img, bg=t.CARD_BG)
            lbl.image = truck_img
            lbl.pack(side=tk.LEFT, padx=(0, 6))
        tk.Label(row, text=item, font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED, wraplength=600, justify="left").pack(side=tk.LEFT)

    # ----- Right Side: Booking Sidebar with Calendar Widget -----
    right_sidebar = tk.Frame(container, bg=t.FIELD_BG, padx=20, pady=30)
    right_sidebar.grid(row=0, column=1, sticky="nsew")

    tk.Label(right_sidebar, text="Price Summary", font=(t.FONT, 14, "bold"), bg=t.FIELD_BG, fg=t.TEXT).pack(anchor="w", pady=(5, 5))
    tk.Label(right_sidebar, text=f"From {tour['price']}", font=(t.FONT, 16, "bold"), bg=t.FIELD_BG, fg=t.PRIMARY).pack(anchor="w", pady=(0, 15))

    # Which dates can be booked comes from the event itself, not from fixed days.
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    allowed_weekdays = set()
    allowed_date = None
    if tour.get("is_recurring") == "Recurring":
        allowed_weekdays = {weekday_names.index(d.strip()) for d in (tour.get("recur_day") or "").split(",") if d.strip() in weekday_names}
    if not allowed_weekdays:
        try:
            allowed_date = date.fromisoformat((tour.get("event_datetime") or "")[:10])
        except ValueError:
            allowed_date = None
    if allowed_weekdays:
        availability_text = "Select Date (" + ", ".join(weekday_names[i][:3] for i in sorted(allowed_weekdays)) + "):"
    else:
        availability_text = "Event date:"

    tk.Label(right_sidebar, text=availability_text, font=(t.FONT, 10, "bold"), bg=t.FIELD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(0, 5))

    # Calendar Widget State
    today = date.today()
    start_day = allowed_date if allowed_date and allowed_date >= today else today

    # Auto-select the first available upcoming date so capacity shows dynamically on open
    initial_selection = None
    if allowed_date and allowed_date >= today:
        initial_selection = allowed_date
    elif allowed_weekdays:
        cur = today
        for _ in range(60):
            if cur.weekday() in allowed_weekdays:
                initial_selection = cur
                start_day = cur
                break
            cur = date.fromordinal(cur.toordinal() + 1)

    cal_state = {"year": start_day.year, "month": start_day.month, "selected": initial_selection}

    cal_frame = tk.Frame(right_sidebar, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
    cal_frame.pack(fill=tk.X, pady=5)

    header_frame = tk.Frame(cal_frame, bg=t.CARD_BG)
    header_frame.pack(fill=tk.X, padx=5, pady=5)

    month_label = tk.Label(header_frame, text="", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.TEXT)
    month_label.pack(side=tk.LEFT, padx=5)

    days_grid = tk.Frame(cal_frame, bg=t.CARD_BG)
    days_grid.pack(fill=tk.BOTH, padx=5, pady=5)

    selected_label = tk.Label(right_sidebar, text="Selected: None", font=(t.FONT, 9, "bold"), bg=t.FIELD_BG, fg="#e74c3c")
    selected_label.pack(anchor="w", pady=(10, 5))

    # Capacity Bar Widget
    capacity_bar = CapacityBar(right_sidebar, remaining=capacity["total"], total=capacity["total"], width=130, height=14, bg=t.FIELD_BG)
    capacity_bar.pack(anchor="w", pady=(0, 8))

    # ----- guests and total price -----
    unit_price = price_to_int(tour["price"])
    guests_row = tk.Frame(right_sidebar, bg=t.FIELD_BG)
    guests_row.pack(fill=tk.X, pady=(5, 0))
    tk.Label(guests_row, text="Guests:", font=(t.FONT, 10, "bold"), bg=t.FIELD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT)
    guests_var = tk.IntVar(value=1)

    initial_limit = capacity["total"] if is_partner else min(MAX_GUESTS_PER_BOOKING, capacity["total"])
    guests_spin = tk.Spinbox(guests_row, from_=1, to=max(1, initial_limit), width=5 if is_partner else 4,
                             textvariable=guests_var, font=(t.FONT, 10))
    guests_spin.pack(side=tk.LEFT, padx=8)

    if is_partner:
        partner_lbl = tk.Label(right_sidebar, text=" Extended Capacity (OTA Partner)",
                 font=(t.FONT, 8, "bold"), bg=t.FIELD_BG, fg=t.PRIMARY)
        shield_img = ic.get_icon("shield", size=13, color=t.PRIMARY, master=right_sidebar)
        if shield_img:
            partner_lbl.config(image=shield_img, compound=tk.LEFT)
            partner_lbl.image = shield_img
        partner_lbl.pack(anchor="w", pady=(2, 4))

        client_box = tk.Frame(right_sidebar, bg=t.FIELD_BG)
        client_box.pack(fill=tk.X, pady=(4, 0))
        tk.Label(client_box, text="Customer / Group Name (Optional):", font=(t.FONT, 9, "bold"),
                 bg=t.FIELD_BG, fg=t.TEXT_MUTED).pack(anchor="w")
        client_entry = tk.Entry(client_box, font=(t.FONT, 10), bg=t.CARD_BG, relief="solid", bd=1)
        client_entry.pack(fill=tk.X, ipady=3, pady=(2, 4))
    else:
        client_entry = None

    total_label = tk.Label(right_sidebar, text="", font=(t.FONT, 12, "bold"), bg=t.FIELD_BG, fg=t.TEXT)
    total_label.pack(anchor="w", pady=(8, 0))

    def current_guests():
        try:
            return max(1, int(guests_var.get()))
        except (tk.TclError, ValueError):
            return 1

    def update_total(*args):
        total_label.config(text=f"Total: {unit_price * current_guests()} AED")

    guests_var.trace_add("write", update_total)
    update_total()

    def refresh_capacity():
        """Shows the seats left on the chosen date and stops the guests box from going above them."""
        chosen = cal_state["selected"]
        info = get_event_capacity(tour["id"], chosen)
        fully_booked = False
        if chosen is None:
            limit = info["total"] if is_partner else min(MAX_GUESTS_PER_BOOKING, info["total"])
            capacity_bar.set_capacity(info["total"], info["total"], suffix="(pick a date)")
        else:
            left = info["remaining"]
            fully_booked = left <= 0
            limit = left if is_partner else min(MAX_GUESTS_PER_BOOKING, left)
            capacity_bar.set_capacity(left, info["total"])

        limit = max(1, limit)
        guests_spin.config(to=limit)
        if current_guests() > limit:
            guests_var.set(limit)

        if is_partner:
            if fully_booked:
                add_list_btn.config(state=tk.DISABLED, text="Fully booked")
                pay_now_btn.config(state=tk.DISABLED, text="Fully booked")
            else:
                add_list_btn.config(state=tk.NORMAL, text=" Add to Shopping List")
                pay_now_btn.config(state=tk.NORMAL, text=" Pay Now (Single Event)")
        else:
            if fully_booked:
                book_btn.config(state=tk.DISABLED, text="Fully booked")
            else:
                book_btn.config(state=tk.NORMAL, text="Proceed to Booking")

        return info

    def draw_calendar():
        for widget in days_grid.winfo_children():
            widget.destroy()

        y, m = cal_state["year"], cal_state["month"]
        month_label.config(text=f"{calendar.month_name[m]} {y}")

        weekdays = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for col, day_name in enumerate(weekdays):
            tk.Label(days_grid, text=day_name, font=(t.FONT, 8, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED, width=3).grid(row=0, column=col, padx=1, pady=1)

        cal = calendar.monthcalendar(y, m)
        for row_idx, week in enumerate(cal):
            for col_idx, day in enumerate(week):
                if day == 0:
                    tk.Label(days_grid, text="", bg=t.CARD_BG, width=3).grid(row=row_idx+1, column=col_idx, padx=1, pady=1)
                else:
                    d_obj = date(y, m, day)
                    is_past = d_obj < today
                    is_demo_day = (d_obj.weekday() in allowed_weekdays) if allowed_weekdays else (d_obj == allowed_date)
                    is_unavailable = is_past or not is_demo_day

                    if is_unavailable:
                        btn = tk.Button(days_grid, text=str(day), font=(t.FONT, 8), bg=t.CHIP_BG, fg=t.TEXT_MUTED, width=3, state="disabled", relief="flat")
                    else:
                        is_selected = cal_state["selected"] == d_obj
                        bg_col = t.PRIMARY if is_selected else t.CARD_BG
                        fg_col = "white" if is_selected else t.TEXT

                        def make_click(target_date):
                            return lambda: select_date(target_date)

                        btn = tk.Button(days_grid, text=str(day), font=(t.FONT, 8, "bold" if is_selected else "normal"),
                                        bg=bg_col, fg=fg_col, width=3, relief="flat", command=make_click(d_obj))
                    btn.grid(row=row_idx+1, column=col_idx, padx=1, pady=1)

    def select_date(d_obj):
        cal_state["selected"] = d_obj
        selected_label.config(text=f"Selected: {d_obj.strftime('%b %d, %Y')}", fg="#27ae60")
        refresh_capacity()
        draw_calendar()

    def prev_month():
        if cal_state["month"] == 1:
            cal_state["month"] = 12
            cal_state["year"] -= 1
        else:
            cal_state["month"] -= 1
        draw_calendar()

    def next_month():
        if cal_state["month"] == 12:
            cal_state["month"] = 1
            cal_state["year"] += 1
        else:
            cal_state["month"] += 1
        draw_calendar()

    # Calendar nav buttons with Lucide chevron icons
    tk.Button(header_frame, text=">", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT, bd=0, relief="flat", command=next_month, cursor="hand2").pack(side=tk.RIGHT, padx=2)
    tk.Button(header_frame, text="<", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT, bd=0, relief="flat", command=prev_month, cursor="hand2").pack(side=tk.RIGHT, padx=2)

    draw_calendar()
    if cal_state["selected"]:
        select_date(cal_state["selected"])
    else:
        refresh_capacity()

    # ----- Booking Action Handlers -----
    if is_partner:
        def handle_add_to_cart():
            if not cal_state["selected"]:
                messagebox.showerror("Error", "Please select an available date for this tour.")
                return
            chosen_date = cal_state["selected"]
            guests = current_guests()
            info = refresh_capacity()
            if guests > info["remaining"]:
                messagebox.showerror("Not enough seats", f"Only {info['remaining']} seat(s) remaining on {chosen_date.strftime('%b %d, %Y')}.")
                return

            c_name = client_entry.get().strip() if client_entry else ""
            res = add_to_cart(email, tour["id"], chosen_date.isoformat(), guests, c_name)
            if not res["success"]:
                messagebox.showerror("Failed to Add", res["message"])
                return

            if messagebox.askyesno(
                "Added to Shopping List",
                f"Added {tour['title']} ({guests} guests) to your shopping list.\n\nGo to Shopping List now to review and pay?"
            ):
                from welcome.partner_welcome import show_partner_welcome
                show_partner_welcome(root, email, tab="cart")
            else:
                from welcome.partner_welcome import show_partner_welcome
                show_partner_welcome(root, email, tab="explore")

        def handle_partner_pay_now():
            if not cal_state["selected"]:
                messagebox.showerror("Error", "Please select an available date for this tour.")
                return
            chosen_date = cal_state["selected"]
            guests = current_guests()
            info = refresh_capacity()
            if guests > info["remaining"]:
                messagebox.showerror("Not enough seats", f"Only {info['remaining']} seat(s) remaining on {chosen_date.strftime('%b %d, %Y')}.")
                return

            c_name = client_entry.get().strip() if client_entry else ""
            tot = unit_price * guests

            def on_pay_success():
                res = create_booking(email, tour["id"], chosen_date.isoformat(), guests, is_partner=True, client_name=c_name)
                if not res["success"]:
                    messagebox.showerror("Booking failed", res["message"])
                    refresh_capacity()
                    return
                booking = res["booking"]
                messagebox.showinfo(
                    "OTA Booking Confirmed",
                    f"Booking Confirmed!\n\nTicket Code: {format_ticket_code(booking['ticket_code'])}\n"
                    f"Event: {tour['title']}\nDate: {chosen_date.strftime('%b %d, %Y')}\nGuests: {guests}\n"
                    f"Group: {c_name or 'N/A'}\nTotal: {tot} AED"
                )
                from welcome.partner_welcome import show_partner_welcome
                show_partner_welcome(root, email, tab="bookings")

            items = [{
                "title": tour["title"],
                "date": chosen_date.strftime('%b %d, %Y'),
                "guests": guests,
                "total": tot,
                "client_name": c_name
            }]
            show_demo_payment_modal(root, "OTA Booking - Single Event", items, tot, on_pay_success)

        add_list_btn = tk.Button(right_sidebar, text=" Add to Shopping List", font=(t.FONT, 11, "bold"), bd=0, relief="flat",
                                 bg=t.ACCENT, fg="white", activebackground=t.PRIMARY_HOVER, cursor="hand2", command=handle_add_to_cart)
        plus_img = ic.get_icon("plus", size=16, color="#ffffff", master=right_sidebar)
        if plus_img:
            add_list_btn.config(image=plus_img, compound=tk.LEFT)
            add_list_btn.image = plus_img
        add_list_btn.pack(fill=tk.X, pady=(15, 6), ipady=8)
        t.add_hover(add_list_btn, t.ACCENT, "#e67e22")

        pay_now_btn = tk.Button(right_sidebar, text=" Pay Now (Single Event)", font=(t.FONT, 10, "bold"), bd=0, relief="flat",
                                bg=t.PRIMARY, fg="white", activebackground=t.PRIMARY_HOVER, cursor="hand2", command=handle_partner_pay_now)
        pay_img = ic.get_icon("payment", size=15, color="#ffffff", master=right_sidebar)
        if pay_img:
            pay_now_btn.config(image=pay_img, compound=tk.LEFT)
            pay_now_btn.image = pay_img
        pay_now_btn.pack(fill=tk.X, pady=(0, 6), ipady=7)
        t.add_hover(pay_now_btn, t.PRIMARY, t.PRIMARY_HOVER)

        view_cart_btn = tk.Button(right_sidebar, text=" View Shopping List", font=(t.FONT, 9), bd=0, relief="flat",
                                  bg=t.CHIP_BG, fg=t.TEXT, cursor="hand2",
                                  command=lambda: (show_partner_welcome(root, email, tab="cart")
                                                   if True else None))
        cart_img = ic.get_icon("cart", size=14, color=t.TEXT, master=right_sidebar)
        if cart_img:
            view_cart_btn.config(image=cart_img, compound=tk.LEFT)
            view_cart_btn.image = cart_img

        def show_partner_welcome(r, e, tab):
            from welcome.partner_welcome import show_partner_welcome as _spw
            _spw(r, e, tab=tab)

        view_cart_btn.pack(fill=tk.X, pady=(0, 0), ipady=5)
        t.add_hover(view_cart_btn, t.CHIP_BG, t.CHIP_HOVER)

    else:
        def handle_booking():
            if not cal_state["selected"]:
                messagebox.showerror("Error", "Please select an available date for your tour.")
                return
            chosen_date = cal_state["selected"]
            guests = current_guests()
            info = refresh_capacity()
            if guests > info["remaining"]:
                if info["remaining"] <= 0:
                    messagebox.showerror("Fully booked", "This event is fully booked on that date. Please choose another date.")
                else:
                    messagebox.showerror("Not enough seats", f"Only {info['remaining']} seat(s) are left on that date.")
                return

            tot = unit_price * guests

            def on_pay_success():
                result = create_booking(email, tour["id"], chosen_date.isoformat(), guests, is_partner=False)
                if not result["success"]:
                    messagebox.showerror("Booking failed", result["message"])
                    refresh_capacity()
                    return

                booking = result["booking"]
                messagebox.showinfo(
                    "Booking confirmed",
                    f"Your booking is confirmed.\n\nTicket code: {format_ticket_code(booking['ticket_code'])}\n"
                    f"Show this code at the entrance. Find it again in My Bookings.",
                )
                from welcome.customer_welcome import show_customer_welcome
                show_customer_welcome(root, email, "bookings")

            items = [{
                "title": tour["title"],
                "date": chosen_date.strftime('%b %d, %Y'),
                "guests": guests,
                "total": tot
            }]
            show_demo_payment_modal(root, "Customer Tour Booking", items, tot, on_pay_success)

        book_btn = tk.Button(right_sidebar, text="Proceed to Booking", font=(t.FONT, 11, "bold"), bd=0, relief="flat",
                             bg=t.ACCENT, fg="white", activebackground=t.PRIMARY_HOVER, cursor="hand2", command=handle_booking)
        book_btn.pack(fill=tk.X, pady=(20, 0), ipady=10)
        t.add_hover(book_btn, t.ACCENT, "#e67e22")
