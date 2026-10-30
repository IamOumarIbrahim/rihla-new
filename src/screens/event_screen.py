import calendar
from datetime import date
import tkinter as tk
from tkinter import messagebox
import navigate
import theme as t
from ui import clear_window

def show_event_screen(root, email, tour):
    clear_window(root)

    container = tk.Frame(root, bg=t.CARD_BG)
    container.pack(fill=tk.BOTH, expand=True)
    container.rowconfigure(0, weight=1)
    container.columnconfigure(0, weight=7, uniform="cols")
    container.columnconfigure(1, weight=3, uniform="cols")

    # ----- Left Side: Event Details -----
    left_frame = tk.Frame(container, bg=t.CARD_BG, padx=40, pady=30)
    left_frame.grid(row=0, column=0, sticky="nsew")

    back_btn = tk.Button(left_frame, text="← Back to Explore", font=(t.FONT, 10), bg=t.CARD_BG, fg=t.PRIMARY, bd=0, relief="flat", cursor="hand2", command=lambda: navigate.show_welcome(root, email))
    back_btn.pack(anchor="w", pady=(0, 15))

    tk.Label(left_frame, text=tour["title"], font=(t.FONT, 22, "bold"), bg=t.CARD_BG, fg=t.TEXT, wraplength=600, justify="left").pack(anchor="w", pady=5)
    
    meta_row = tk.Frame(left_frame, bg=t.CARD_BG)
    meta_row.pack(anchor="w", pady=5)
    tk.Label(meta_row, text=tour["rating"], font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.ACCENT).pack(side=tk.LEFT, padx=(0, 15))
    tk.Label(meta_row, text=f"Category: {tour['category']}", font=(t.FONT, 11), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT)

    tk.Label(left_frame, text="Overview", font=(t.FONT, 14, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", pady=(20, 5))
    tk.Label(left_frame, text=tour["desc"], font=(t.FONT, 11), bg=t.CARD_BG, fg=t.TEXT_MUTED, wraplength=600, justify="left").pack(anchor="w", pady=5)

    tk.Label(left_frame, text="Event Details", font=(t.FONT, 14, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", pady=(20, 5))
    recurrence_text = tour.get("is_recurring") or "One-Time"
    if recurrence_text == "Recurring" and tour.get("recur_day") not in (None, "", "None", "N/A"):
        recurrence_text += f" ({tour['recur_day']})"
    details = [
        f"- Venue: {tour.get('venue_name') or 'To be announced'}",
        f"- Date and time: {tour.get('event_datetime') or 'To be announced'}",
        f"- Type: {recurrence_text}",
    ]
    for item in details:
        tk.Label(left_frame, text=item, font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=2)

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
    cal_state = {"year": start_day.year, "month": start_day.month, "selected": None}

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
                    # Bookable days come from the event (recurring weekdays, or its single date)
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

    def handle_booking():
        if not cal_state["selected"]:
            messagebox.showerror("Error", "Please select an available date for your tour.")
            return
        messagebox.showinfo("Success", f"Proceeding to secure booking for {tour['title']} on {cal_state['selected'].strftime('%b %d, %Y')}!")

    book_btn = tk.Button(right_sidebar, text="Proceed to Booking", font=(t.FONT, 11, "bold"), bd=0, relief="flat",
                         bg=t.ACCENT, fg="white", activebackground=t.PRIMARY_HOVER, cursor="hand2", command=handle_booking)
    book_btn.pack(fill=tk.X, pady=(20, 0), ipady=10)
    t.add_hover(book_btn, t.ACCENT, "#e67e22")