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
from payment import show_demo_payment_modal, show_booking_details_window
import icons as ic
from event_images import CoverImage, load_image
from map_link import venue_label


# on this page the text before the colon ("Venue:", "Guests:") is black, the value keeps its own color
LABEL_FG = "#000000"


# a black 'label:' and its value next to each other, gives back (row, value_label)
def labeled_row(parent, label, value, font, bg, fg, **value_opts):
    row = tk.Frame(parent, bg=bg)
    tk.Label(row, text=label + ":", font=font, bg=bg, fg=LABEL_FG).pack(side=tk.LEFT)
    value_lbl = tk.Label(row, text=value, font=font, bg=bg, fg=fg, **value_opts)
    value_lbl.pack(side=tk.LEFT, padx=(4, 0))
    return row, value_lbl


def show_event_screen(root, email, tour, is_partner=False):
    clear_window(root)
    # get the capacity again from the db because the vehicles can change after the list was loaded
    capacity = get_event_capacity(tour["id"])

    container = tk.Frame(root, bg=t.CARD_BG)
    container.pack(fill=tk.BOTH, expand=True)
    container.rowconfigure(0, weight=1)
    container.columnconfigure(0, weight=7, uniform="cols")
    container.columnconfigure(1, weight=3, uniform="cols")

    # ====== Left side: event details ======
    left_frame = tk.Frame(container, bg=t.CARD_BG, padx=40, pady=30)
    left_frame.grid(row=0, column=0, sticky="nsew")

    def go_back():
        if is_partner:
            from welcome.partner_welcome import show_partner_welcome
            show_partner_welcome(root, email, tab="explore")
        else:
            navigate.show_welcome(root, email)

    back_btn = tk.Button(left_frame, text=ic.emoji("back") + " Back", font=(t.FONT, 10), bg=t.CARD_BG, fg=t.PRIMARY,
                         bd=0, relief="flat", cursor="hand2", command=go_back)
    back_img = ic.get_icon("back", size=14, color=t.PRIMARY, master=left_frame)
    if back_img:
        back_btn.config(image=back_img, compound=tk.LEFT)
        back_btn.image = back_img
    back_btn.pack(anchor="w", pady=(0, 15))
    event_pic = load_image(tour["id"])
    if event_pic is not None:
        CoverImage(left_frame, event_pic, height=220).pack(fill=tk.X, pady=(0, 15))

    tk.Label(left_frame, text=tour["title"], font=(t.FONT, 22, "bold"), bg=t.CARD_BG, fg=t.TEXT,
             wraplength=600, justify="left").pack(anchor="w", pady=5)

    meta_row = tk.Frame(left_frame, bg=t.CARD_BG)
    meta_row.pack(anchor="w", pady=5)

    star_lbl = tk.Label(meta_row, text=ic.emoji("star") + " " + str(tour["rating"]), font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.ACCENT)
    star_img = ic.get_icon("star", size=14, color=t.ACCENT, master=left_frame)
    if star_img:
        star_lbl.config(image=star_img, compound=tk.LEFT)
        star_lbl.image = star_img
    star_lbl.pack(side=tk.LEFT, padx=(0, 15))
    cat_row, cat_value = labeled_row(meta_row, "Category", tour["category"], (t.FONT, 11), t.CARD_BG, t.TEXT_MUTED)
    cat_row.pack(side=tk.LEFT)

    tk.Label(left_frame, text="Overview", font=(t.FONT, 14, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", pady=(20, 5))
    tk.Label(left_frame, text=tour["desc"], font=(t.FONT, 11), bg=t.CARD_BG, fg=t.TEXT_MUTED,
             wraplength=600, justify="left").pack(anchor="w", pady=5)

    tk.Label(left_frame, text="Event Details", font=(t.FONT, 14, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", pady=(20, 5))
    recurrence_text = tour.get("is_recurring")
    if not recurrence_text:
        recurrence_text = "One-Time"
    if recurrence_text == "One-Time":
        recurrence_text = "One-Time Event"
    if recurrence_text == "Recurring" and tour.get("recur_day") not in (None, "", "None", "N/A"):
        recurrence_text += " (" + str(tour["recur_day"]) + ")"

    venue_text = tour.get("venue_name")
    if not venue_text:
        venue_text = "To be announced"
    when_text = tour.get("event_datetime")
    if not when_text:
        when_text = "To be announced"
    maps_url = tour.get("maps_url")
    if not maps_url:
        maps_url = ""

    # detail rows with the icons
    details_data = [
        ("map_pin", "Venue", venue_text),
        ("calendar", "Date and time", when_text),
        ("repeat", "Type", recurrence_text),
    ]
    for icon_key, detail_label, detail_value in details_data:
        row = tk.Frame(left_frame, bg=t.CARD_BG)
        row.pack(anchor="w", pady=2)
        dimg = ic.get_icon(icon_key, size=13, color=t.TEXT_MUTED, master=left_frame)
        if dimg:
            lbl = tk.Label(row, image=dimg, bg=t.CARD_BG)
            lbl.image = dimg
            lbl.pack(side=tk.LEFT, padx=(0, 6))
        if icon_key == "map_pin":
            tk.Label(row, text=ic.emoji(icon_key) + " Venue:", font=(t.FONT, 10), bg=t.CARD_BG, fg=LABEL_FG).pack(side=tk.LEFT)
            venue_label(row, venue_text, tour.get("maps_url"), font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT, padx=(4, 0))
            if maps_url.strip():
                tk.Label(row, text="|", font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT, padx=6)
                venue_label(row, "Open in Google Maps", tour.get("maps_url"), font=(t.FONT, 10), bg=t.CARD_BG).pack(side=tk.LEFT)
        else:
            detail_row, detail_lbl = labeled_row(row, ic.emoji(icon_key) + " " + detail_label, detail_value, (t.FONT, 10), t.CARD_BG, t.TEXT_MUTED)
            detail_row.pack(side=tk.LEFT)

    tk.Label(left_frame, text="Capacity and Vehicles", font=(t.FONT, 14, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", pady=(20, 5))

    left_cap_bar = CapacityBar(left_frame, remaining=capacity["total"], total=capacity["total"], width=140, height=14, bg=t.CARD_BG)
    left_cap_bar.pack(anchor="w", pady=(2, 6))

    # (label, value), label None means its just a sentence without the colon
    capacity_lines = [("Total Capacity", str(capacity["total"]) + " guests per date")]
    if capacity["vehicles"]:
        for vehicle in capacity["vehicles"]:
            line = (str(vehicle["count"]) + " x " + str(vehicle["vehicle_type"]) + " ("
                    + str(vehicle["seats_each"]) + " seats each)")
            capacity_lines.append(("Vehicles", line))
        capacity_lines.append((None, "The seats of these vehicles set the limit for this event."))
    else:
        capacity_lines.append(("Vehicles", "none assigned to this event"))

    for item_label, item in capacity_lines:
        row = tk.Frame(left_frame, bg=t.CARD_BG)
        row.pack(anchor="w", pady=2)
        truck_img = ic.get_icon("truck", size=13, color=t.TEXT_MUTED, master=left_frame)
        if truck_img:
            lbl = tk.Label(row, image=truck_img, bg=t.CARD_BG)
            lbl.image = truck_img
            lbl.pack(side=tk.LEFT, padx=(0, 6))
        if item_label:
            line_row, line_lbl = labeled_row(row, item_label, item, (t.FONT, 10), t.CARD_BG, t.TEXT_MUTED, wraplength=600, justify="left")
            line_row.pack(side=tk.LEFT)
        else:
            tk.Label(row, text=item, font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED, wraplength=600, justify="left").pack(side=tk.LEFT)

    # ====== Right side: booking with the calendar ======
    right_sidebar = tk.Frame(container, bg=t.FIELD_BG, padx=20, pady=30)
    right_sidebar.grid(row=0, column=1, sticky="nsew")

    tk.Label(right_sidebar, text="Price Summary", font=(t.FONT, 14, "bold"), bg=t.FIELD_BG, fg=t.TEXT).pack(anchor="w", pady=(5, 5))
    tk.Label(right_sidebar, text="From " + str(tour["price"]), font=(t.FONT, 16, "bold"), bg=t.FIELD_BG, fg=t.PRIMARY).pack(anchor="w", pady=(0, 15))

    # the dates you can book come from the event and not from fixed days
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    allowed_weekdays = set()
    allowed_date = None
    if tour.get("is_recurring") == "Recurring":
        recur_day = tour.get("recur_day")
        if not recur_day:
            recur_day = ""
        for d in recur_day.split(","):
            if d.strip() in weekday_names:
                allowed_weekdays.add(weekday_names.index(d.strip()))
    if not allowed_weekdays:
        dt_text = tour.get("event_datetime")
        if not dt_text:
            dt_text = ""
        try:
            allowed_date = date.fromisoformat(dt_text[:10])
        except ValueError:
            allowed_date = None
    if allowed_weekdays:
        short_days = ""
        for i in range(7):
            if i in allowed_weekdays:
                if short_days != "":
                    short_days = short_days + ", "
                short_days = short_days + weekday_names[i][:3]
        availability_text = "Select Date (" + short_days + "):"
    else:
        availability_text = "Event date:"

    tk.Label(right_sidebar, text=availability_text, font=(t.FONT, 10, "bold"), bg=t.FIELD_BG, fg=LABEL_FG).pack(anchor="w", pady=(0, 5))

    # Calendar

    today = date.today()
    if allowed_date and allowed_date >= today:
        start_day = allowed_date
    else:
        start_day = today

    # pick the first date that is free so the capacity already shows when the page opens
    initial_selection = None
    if allowed_date and allowed_date >= today:
        initial_selection = allowed_date
    elif allowed_weekdays:
        cur = today
        for k in range(60):
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

    selected_row, selected_label = labeled_row(right_sidebar, "Selected", "None", (t.FONT, 9, "bold"), t.FIELD_BG, "#e74c3c")
    selected_row.pack(anchor="w", pady=(10, 5))

    capacity_bar = CapacityBar(right_sidebar, remaining=capacity["total"], total=capacity["total"], width=130, height=14, bg=t.FIELD_BG)
    capacity_bar.pack(anchor="w", pady=(0, 8))

    # Guests and total price
    unit_price = price_to_int(tour["price"])
    guests_row = tk.Frame(right_sidebar, bg=t.FIELD_BG)
    guests_row.pack(fill=tk.X, pady=(5, 0))
    tk.Label(guests_row, text="Guests:", font=(t.FONT, 10, "bold"), bg=t.FIELD_BG, fg=LABEL_FG).pack(side=tk.LEFT)
    guests_var = tk.IntVar(value=1)

    if is_partner:
        initial_limit = capacity["total"]
        spin_width = 5
    else:
        initial_limit = capacity["total"]
        if MAX_GUESTS_PER_BOOKING < initial_limit:
            initial_limit = MAX_GUESTS_PER_BOOKING
        spin_width = 4
    if initial_limit < 1:
        initial_limit = 1
    guests_spin = tk.Spinbox(guests_row, from_=1, to=initial_limit, width=spin_width,
                             textvariable=guests_var, font=(t.FONT, 10))
    guests_spin.pack(side=tk.LEFT, padx=8)

    if is_partner:
        partner_lbl = tk.Label(right_sidebar, text=ic.emoji("shield") + " Extended Capacity (OTA Partner)",
                               font=(t.FONT, 8, "bold"), bg=t.FIELD_BG, fg=t.PRIMARY)
        shield_img = ic.get_icon("shield", size=13, color=t.PRIMARY, master=right_sidebar)
        if shield_img:
            partner_lbl.config(image=shield_img, compound=tk.LEFT)
            partner_lbl.image = shield_img
        partner_lbl.pack(anchor="w", pady=(2, 4))

        client_box = tk.Frame(right_sidebar, bg=t.FIELD_BG)
        client_box.pack(fill=tk.X, pady=(4, 0))
        tk.Label(client_box, text="Customer / Group Name (Optional):", font=(t.FONT, 9, "bold"),
                 bg=t.FIELD_BG, fg=LABEL_FG).pack(anchor="w")
        client_entry = tk.Entry(client_box, font=(t.FONT, 10), bg=t.CARD_BG, relief="solid", bd=1)
        client_entry.pack(fill=tk.X, ipady=3, pady=(2, 4))
    else:
        client_entry = None

    total_row, total_label = labeled_row(right_sidebar, "Total", "", (t.FONT, 12, "bold"), t.FIELD_BG, t.TEXT)
    total_row.pack(anchor="w", pady=(8, 0))

    def current_guests():
        try:
            n = int(guests_var.get())
        except (tk.TclError, ValueError):
            return 1
        if n < 1:
            n = 1
        return n

    # total = price * guests
    def update_total(*args):
        total_label.config(text=str(unit_price * current_guests()) + " AED")

    guests_var.trace_add("write", update_total)
    update_total()

    # shows the seats left on the date and the guests box cant go higher than that
    def refresh_capacity():
        chosen = cal_state["selected"]
        info = get_event_capacity(tour["id"], chosen)
        fully_booked = False
        if chosen is None:
            if is_partner:
                limit = info["total"]
            else:
                limit = info["total"]
                if MAX_GUESTS_PER_BOOKING < limit:
                    limit = MAX_GUESTS_PER_BOOKING
            capacity_bar.set_capacity(info["total"], info["total"], suffix="(pick a date)")
        else:
            seats_left = info["remaining"]
            fully_booked = seats_left <= 0
            if is_partner:
                limit = seats_left
            else:
                limit = seats_left
                if MAX_GUESTS_PER_BOOKING < limit:
                    limit = MAX_GUESTS_PER_BOOKING
            capacity_bar.set_capacity(seats_left, info["total"])

        if limit < 1:
            limit = 1
        guests_spin.config(to=limit)
        if current_guests() > limit:
            guests_var.set(limit)

        if is_partner:
            if fully_booked:
                add_list_btn.config(state=tk.DISABLED, text="Fully booked")
                pay_now_btn.config(state=tk.DISABLED, text="Fully booked")
            else:
                add_list_btn.config(state=tk.NORMAL, text=ic.emoji("cart") + " Add to List")
                pay_now_btn.config(state=tk.NORMAL, text="Pay Now")
        else:
            if fully_booked:
                book_btn.config(state=tk.DISABLED, text="Fully booked")
            else:
                book_btn.config(state=tk.NORMAL, text="Proceed to Booking")

        return info

    def draw_calendar():
        for widget in days_grid.winfo_children():
            widget.destroy()

        y = cal_state["year"]
        m = cal_state["month"]
        month_label.config(text=calendar.month_name[m] + " " + str(y))

        weekdays = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for col in range(len(weekdays)):
            tk.Label(days_grid, text=weekdays[col], font=(t.FONT, 8, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED, width=3).grid(row=0, column=col, padx=1, pady=1)

        cal = calendar.monthcalendar(y, m)
        for row_idx in range(len(cal)):
            week = cal[row_idx]
            for col_idx in range(len(week)):
                day = week[col_idx]
                if day == 0:
                    tk.Label(days_grid, text="", bg=t.CARD_BG, width=3).grid(row=row_idx+1, column=col_idx, padx=1, pady=1)
                else:
                    d_obj = date(y, m, day)
                    is_past = d_obj < today
                    if allowed_weekdays:
                        is_demo_day = d_obj.weekday() in allowed_weekdays
                    else:
                        is_demo_day = d_obj == allowed_date
                    is_unavailable = is_past or not is_demo_day

                    if is_unavailable:
                        btn = tk.Button(days_grid, text=str(day), font=(t.FONT, 8), bg=t.CHIP_BG, fg=t.TEXT_MUTED, width=3, state="disabled", relief="flat")
                    else:
                        is_selected = cal_state["selected"] == d_obj
                        if is_selected:
                            bg_col = t.PRIMARY
                            fg_col = "white"
                            weight = "bold"
                        else:
                            bg_col = t.CARD_BG
                            fg_col = t.TEXT
                            weight = "normal"

                        def on_day_click(target_date=d_obj):
                            select_date(target_date)

                        btn = tk.Button(days_grid, text=str(day), font=(t.FONT, 8, weight),
                                        bg=bg_col, fg=fg_col, width=3, relief="flat", command=on_day_click)
                    btn.grid(row=row_idx+1, column=col_idx, padx=1, pady=1)

    def select_date(d_obj):
        cal_state["selected"] = d_obj
        selected_label.config(text=d_obj.strftime('%b %d, %Y'), fg="#27ae60")
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

    tk.Button(header_frame, text=">", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT, bd=0, relief="flat", command=next_month, cursor="hand2").pack(side=tk.RIGHT, padx=2)
    tk.Button(header_frame, text="<", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT, bd=0, relief="flat", command=prev_month, cursor="hand2").pack(side=tk.RIGHT, padx=2)

    draw_calendar()

    # Booking buttons
    if is_partner:
        def handle_add_to_cart():
            if not cal_state["selected"]:
                messagebox.showerror("Error", "Please select an available date for this tour.")
                return
            chosen_date = cal_state["selected"]
            guests = current_guests()
            info = refresh_capacity()
            if guests > info["remaining"]:
                messagebox.showerror("Not enough seats", "Only " + str(info["remaining"]) + " seat(s) remaining on " + chosen_date.strftime('%b %d, %Y') + ".")
                return

            c_name = ""
            if client_entry:
                c_name = client_entry.get().strip()
            res = add_to_cart(email, tour["id"], chosen_date.isoformat(), guests, c_name)
            if not res["success"]:
                messagebox.showerror("Failed to Add", res["message"])
                return

            question = ("Added " + str(tour["title"]) + " (" + str(guests) + " guests) to your shopping list."
                        + "\n\nGo to Shopping List now to review and pay?")
            if messagebox.askyesno("Added to Shopping List", question):
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
                messagebox.showerror("Not enough seats", "Only " + str(info["remaining"]) + " seat(s) remaining on " + chosen_date.strftime('%b %d, %Y') + ".")
                return

            c_name = ""
            if client_entry:
                c_name = client_entry.get().strip()
            tot = unit_price * guests

            def on_pay_success(payment):
                res = create_booking(email, tour["id"], chosen_date.isoformat(), guests, is_partner=True, client_name=c_name)
                booking = res.get("booking")
                if not booking:
                    booking = {}
                venue = booking.get("venue_name")
                if not venue:
                    venue = tour.get("venue_name")
                code = None
                if booking:
                    code = format_ticket_code(booking["ticket_code"])
                details = {
                    "title": tour["title"], "base": tot,
                    "venue": venue,
                    "date": chosen_date.strftime('%b %d, %Y'), "time": booking.get("event_time"),
                    "guests": guests, "client_name": c_name,
                    "ticket_code": code,
                }

                def after_close():
                    if res["success"]:
                        from welcome.partner_welcome import show_partner_welcome
                        show_partner_welcome(root, email, tab="bookings")
                    else:
                        refresh_capacity()

                error = None
                if not res["success"]:
                    error = res["message"]
                show_booking_details_window(root, [details], payment, email,
                                            error=error, on_close=after_close)

            items = [{
                "title": tour["title"],
                "date": chosen_date.strftime('%b %d, %Y'),
                "guests": guests,
                "total": tot,
                "client_name": c_name
            }]
            show_demo_payment_modal(root, "OTA Booking - Single Event", items, tot, on_pay_success, email=email)

        add_list_btn = tk.Button(right_sidebar, text="Add to List", font=(t.FONT, 11, "bold"), bd=0, relief="flat",
                                 bg=t.ACCENT, fg="white", activebackground=t.PRIMARY_HOVER, cursor="hand2", command=handle_add_to_cart)
        plus_img = ic.get_icon("plus", size=16, color="#ffffff", master=right_sidebar)
        if plus_img:
            add_list_btn.config(image=plus_img, compound=tk.LEFT)
            add_list_btn.image = plus_img
        add_list_btn.pack(fill=tk.X, pady=(15, 6), ipady=8)
        t.add_hover(add_list_btn, t.ACCENT, "#e67e22")

        pay_now_btn = tk.Button(right_sidebar, text="Pay Now", font=(t.FONT, 10, "bold"), bd=0, relief="flat",
                                bg=t.PRIMARY, fg="white", activebackground=t.PRIMARY_HOVER, cursor="hand2", command=handle_partner_pay_now)
        pay_img = ic.get_icon("payment", size=15, color="#ffffff", master=right_sidebar)
        if pay_img:
            pay_now_btn.config(image=pay_img, compound=tk.LEFT)
            pay_now_btn.image = pay_img
        pay_now_btn.pack(fill=tk.X, pady=(0, 6), ipady=7)
        t.add_hover(pay_now_btn, t.PRIMARY, t.PRIMARY_HOVER)

        def view_cart():
            from welcome.partner_welcome import show_partner_welcome
            show_partner_welcome(root, email, tab="cart")

        view_cart_btn = tk.Button(right_sidebar, text="View List", font=(t.FONT, 9), bd=0, relief="flat",
                                  bg=t.CHIP_BG, fg=t.TEXT, cursor="hand2",
                                  command=view_cart)
        cart_img = ic.get_icon("cart", size=14, color=t.TEXT, master=right_sidebar)
        if cart_img:
            view_cart_btn.config(image=cart_img, compound=tk.LEFT)
            view_cart_btn.image = cart_img

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
                    messagebox.showerror("Not enough seats", "Only " + str(info["remaining"]) + " seat(s) are left on that date.")
                return

            tot = unit_price * guests

            def on_pay_success(payment):
                result = create_booking(email, tour["id"], chosen_date.isoformat(), guests, is_partner=False)
                booking = result.get("booking")
                if not booking:
                    booking = {}
                venue = booking.get("venue_name")
                if not venue:
                    venue = tour.get("venue_name")
                code = None
                if booking:
                    code = format_ticket_code(booking["ticket_code"])
                details = {
                    "title": tour["title"], "base": tot,
                    "venue": venue,
                    "date": chosen_date.strftime('%b %d, %Y'), "time": booking.get("event_time"),
                    "guests": guests,
                    "ticket_code": code,
                }

                def after_close():
                    if result["success"]:
                        from welcome.customer_welcome import show_customer_welcome
                        show_customer_welcome(root, email, "bookings")
                    else:
                        refresh_capacity()

                error = None
                if not result["success"]:
                    error = result["message"]
                show_booking_details_window(root, [details], payment, email,
                                            error=error, on_close=after_close)

            items = [{
                "title": tour["title"],
                "date": chosen_date.strftime('%b %d, %Y'),
                "guests": guests,
                "total": tot
            }]
            show_demo_payment_modal(root, "Customer Tour Booking", items, tot, on_pay_success, email=email)

        book_btn = tk.Button(right_sidebar, text=ic.emoji("ticket") + " Proceed to Booking", font=(t.FONT, 11, "bold"), bd=0, relief="flat",
                             bg=t.ACCENT, fg="white", activebackground=t.PRIMARY_HOVER, cursor="hand2", command=handle_booking)
        book_btn.pack(fill=tk.X, pady=(20, 0), ipady=10)
        t.add_hover(book_btn, t.ACCENT, "#e67e22")

    # this has to run after the booking buttons exist because refresh_capacity() changes them
    if cal_state["selected"]:
        select_date(cal_state["selected"])
    else:
        refresh_capacity()
