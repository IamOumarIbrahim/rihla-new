import os
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from collections import Counter
from .users_welcome import BaseWelcomeScreen
from .table_style import GEAR, TABLE_STYLE, style_tables, heading_text, stripe_tags
from database import (
    get_events_by_vendor, create_event, update_event, delete_event,
    get_vendor_categories, add_vendor_category, delete_vendor_category,
    get_venues_by_vendor, create_venue, update_venue_maps_url, delete_venue, count_active_bookings,
    get_bookings_by_vendor, vendor_cancel_booking, get_event_capacity, DEFAULT_EVENT_CAPACITY, MAX_EVENT_CAPACITY
)
from .cancellation import page_header, cancelled_line, ask_reason, cancel_button
import theme as t
import icons as ic
import event_images
from map_link import venue_label

# Columns of the bookings table: (key, heading, width, anchor, filterable)
BOOKING_COLUMNS = [
    ("event", "Event", 200, "w", True),
    ("date", "Date", 100, "center", True),
    ("time", "Time", 60, "center", False),
    ("guests", "Guests", 60, "center", False),
    ("customer", "Customer", 190, "w", True),
    ("total", "Total (AED)", 100, "e", False),
    ("refund", "Refunded (AED)", 120, "e", False),
    ("status", "Status", 110, "center", True),
]
# Rows of these statuses get a text color; Confirmed and Checked in rows keep the normal text color.
STATUS_COLORS = {"Expired": t.TEXT_MUTED, "Cancelled": "#c0392b"}


class VendorWelcomeScreen(BaseWelcomeScreen):
    def __init__(self, root, email):
        super().__init__(root, email, "Vendor")
        self.root = root
        self.booking_hidden = {}  # column key -> values hidden by its filter

        self.add_nav_button("My Events", self.build_vendor_content, icon="calendar")
        self.add_nav_button("Bookings", self.build_bookings_content, icon="ticket")
        self.add_nav_button("Manage Venues", self.build_venues_content, icon="stadium")
        self.add_nav_button("Manage Categories", self.build_categories_content, icon="tag")
        self.add_nav_button("Add New Event", self.open_add_event_modal, icon="plus")

        self.build_vendor_content()

    def build_vendor_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        tk.Label(self.scrollable_frame, text=f"Welcome back, {self.username}!", font=(t.FONT, 22, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 5))

        action_frame = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        action_frame.pack(fill=tk.X, padx=30, pady=10)
        
        add_btn = tk.Button(action_frame, text=f"{ic.emoji('plus')} Create New Event Listing", font=(t.FONT, 10, "bold"), bg=t.ACCENT, fg="white", relief="flat", command=self.open_add_event_modal)
        add_btn.pack(side=tk.LEFT, ipadx=15, ipady=8)
        t.add_hover(add_btn, t.ACCENT, "#e67e22")

        events = get_events_by_vendor(self.email)

        if not events:
            tk.Label(self.scrollable_frame, text="No event listings found. Create your first one above!", font=(t.FONT, 11, "italic"), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=20)
            return

        for event in events:
            outer = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
            outer.pack(fill=tk.X, padx=30, pady=10, ipady=10)
            card = event_images.build_card_shell(outer, event["id"], text_weight=3, image_weight=1)

            top_row = tk.Frame(card, bg=t.CARD_BG)
            top_row.pack(fill=tk.X, padx=15, pady=5)
            tk.Label(top_row, text=f"{ic.emoji('tag')} Category: {event['category']}", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.PRIMARY).pack(side=tk.LEFT)
            tk.Label(top_row, text=event['price'], font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.ACCENT).pack(side=tk.RIGHT)

            tk.Label(card, text=event['title'], font=(t.FONT, 14, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=15, pady=2)
            venue_display = event.get('venue_name') or 'Unknown Venue'
            recur_suffix = f" ({event['recur_day']})" if event['is_recurring'] == "Recurring" and event['recur_day'] not in (None, "", "None", "N/A") else ""
            venue_row = tk.Frame(card, bg=t.CARD_BG)
            venue_row.pack(anchor="w", padx=15, pady=2)
            venue_label(venue_row, venue_display, event.get('maps_url'), font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT)
            tk.Label(venue_row, text=f"  | {event['event_datetime']} |  {event['is_recurring']}{recur_suffix}", font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT)
            cap = get_event_capacity(event['id'])
            if cap['vehicles']:
                vehicle_count = sum(v['count'] for v in cap['vehicles'])
                capacity_text = f"Capacity: {cap['total']} guests (seats of {vehicle_count} assigned vehicle(s))"
            else:
                capacity_text = f" Capacity: {cap['total']} guests (no vehicles assigned)"
            tk.Label(card, text=capacity_text, font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=2)
            tk.Label(card, text=event['desc'], font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED, wraplength=600, justify="left").pack(anchor="w", padx=15, pady=5)

            btn_row = tk.Frame(card, bg=t.CARD_BG)
            btn_row.pack(anchor="w", padx=15, pady=(5, 10))

            edit_btn = tk.Button(btn_row, text=f"{ic.emoji('edit')} Edit", bg=t.PRIMARY, fg="white", font=(t.FONT, 9, "bold"), relief="flat", command=lambda e=event: self.open_edit_event_modal(e))
            edit_btn.pack(side=tk.LEFT, padx=(0, 10), ipadx=10, ipady=4)
            t.add_hover(edit_btn, t.PRIMARY, t.PRIMARY_HOVER)

            delete_btn = tk.Button(btn_row, text=f"{ic.emoji('trash')} Delete", bg="#e74c3c", fg="white", font=(t.FONT, 9, "bold"), relief="flat", command=lambda eid=event['id']: self.handle_delete(eid))
            delete_btn.pack(side=tk.LEFT, ipadx=10, ipady=4)
            t.add_hover(delete_btn, "#e74c3c", "#c0392b")

    @staticmethod
    def _booking_val(b, col_key):
        if col_key == "event":
            return b["event_title"]
        if col_key == "date":
            return b["booking_date"]
        if col_key == "time":
            return b["event_time"] or "TBA"
        if col_key == "guests":
            return b["guests"]
        if col_key == "customer":
            return b["customer_email"]
        if col_key == "total":
            return f"{float(b['total_price']):,.2f}"
        if col_key == "refund":
            return f"{float(b['refund_amount']):,.2f} ({b['refund_percent']}%)" if b.get("refund_amount") is not None else ""
        if col_key == "status":
            return b["status"]
        return ""

    def build_bookings_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        style_tables()

        page_header(self.scrollable_frame, "Bookings", self.build_bookings_content)

        bookings = get_bookings_by_vendor(self.email)
        live = [b for b in bookings if b["status"] != "Cancelled"]
        refunded = sum(b["refund_amount"] or 0 for b in bookings if b["status"] == "Cancelled")
        summary = (f"{len(live)} booking(s)  |  {sum(b['guests'] for b in live)} guests  |  "
                   f"{sum(b['total_price'] for b in live):,.2f} AED booked  |  {refunded:,.2f} AED refunded")
        tk.Label(self.scrollable_frame, text=summary, font=(t.FONT, 11), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 10))

        if not bookings:
            tk.Label(self.scrollable_frame, text="No customer has booked one of your events yet.", font=(t.FONT, 11, "italic"), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=10)
            return

        visible = [b for b in bookings
                   if all(str(self._booking_val(b, ck)) not in vals for ck, vals in self.booking_hidden.items())]



        frame = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
        frame.pack(fill=tk.X, padx=30, pady=2)
        col_keys = [c[0] for c in BOOKING_COLUMNS]
        tree = ttk.Treeview(frame, columns=col_keys, show="headings", height=min(max(len(visible), 3), 15),
                            style=TABLE_STYLE, selectmode="browse")
        stripe_tags(tree)
        for status, color in STATUS_COLORS.items():
            tree.tag_configure(f"status_{status}", foreground=color)

        for col_key, heading, width, anchor, filterable in BOOKING_COLUMNS:
            if filterable:
                tree.heading(col_key, text=heading_text(heading, bool(self.booking_hidden.get(col_key))), anchor=anchor,
                             command=lambda ck=col_key, h=heading: self._open_booking_filter(ck, h, bookings))
            else:
                tree.heading(col_key, text=heading, anchor=anchor)
            tree.column(col_key, width=width, minwidth=width, anchor=anchor, stretch=col_key in ("event", "customer"))

        for i, b in enumerate(visible):
            tree.insert("", tk.END, iid=str(b["id"]), values=[self._booking_val(b, ck) for ck in col_keys],
                        tags=("odd" if i % 2 else "even", f"status_{b['status']}"))

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Select a row to see its cancellation details, or to cancel it (full refund, reason required).
        by_id = {str(b["id"]): b for b in visible}
        action_row = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        action_row.pack(fill=tk.X, padx=30, pady=(6, 10))
        cancel_btn = cancel_button(action_row)
        cancel_btn.pack(side=tk.LEFT, ipadx=10, ipady=4)


        def selected_booking():
            chosen = tree.selection()
            return by_id.get(chosen[0]) if chosen else None

        def on_select(_event=None):
            b = selected_booking()
            cancel_btn.config(state=tk.NORMAL if b and b["status"] == "Confirmed" else tk.DISABLED)
            if not b:
                return
            if b["status"] == "Cancelled":
                detail.config(text=cancelled_line(b, self.email), fg="#c0392b")
            elif b["status"] == "Confirmed":
                detail.config(text=f"{b['customer_email']}, {b['guests']} guest(s). Cancelling refunds the customer in full.",
                              fg=t.TEXT_MUTED)
            else:
                detail.config(text=f"This booking is {b['status'].lower()} and cannot be cancelled.", fg=t.TEXT_MUTED)

        def on_cancel():
            b = selected_booking()
            if not b:
                return
            reason = ask_reason(self.root, b)
            if reason is None:
                return
            res = vendor_cancel_booking(b["id"], self.email, reason)
            if res["success"]:
                messagebox.showinfo("Booking cancelled", res["message"])
            else:
                messagebox.showerror("Cannot cancel", res["message"])
            self.build_bookings_content()

        tree.bind("<<TreeviewSelect>>", on_select)
        cancel_btn.config(command=on_cancel)

        if not visible:
            tk.Label(self.scrollable_frame, text=f"All rows are hidden by your column filters. Click a {GEAR} heading to change them.",
                     font=(t.FONT, 9, "italic"), bg=t.PAGE_BG, fg="#e74c3c").pack(anchor="w", padx=30)

    def _open_booking_filter(self, col_key, col_name, bookings):
        popup = tk.Toplevel(self.root)
        popup.title(f"Filter: {col_name}")
        popup.configure(bg=t.CARD_BG)
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()

        tk.Label(popup, text=f"{GEAR} Filter {col_name}", font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=15, pady=(15, 10))

        counts = Counter(str(self._booking_val(b, col_key)) for b in bookings)
        hidden = self.booking_hidden.get(col_key, set())
        var_dict = {}
        frame_chk = tk.Frame(popup, bg=t.CARD_BG)
        frame_chk.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        for val in sorted(counts, key=str.lower):
            var = tk.BooleanVar(value=(val not in hidden))
            var_dict[val] = var
            tk.Checkbutton(frame_chk, text=f"{val}  ({counts[val]})", variable=var, bg=t.CARD_BG, font=(t.FONT, 9),
                           fg=t.TEXT, activebackground=t.CARD_BG, anchor="w").pack(fill=tk.X, pady=1)

        def apply_filter():
            self.booking_hidden[col_key] = {val for val, var in var_dict.items() if not var.get()}
            popup.destroy()
            self.build_bookings_content()

        def clear_filter():
            self.booking_hidden.pop(col_key, None)
            popup.destroy()
            self.build_bookings_content()

        btns = tk.Frame(popup, bg=t.CARD_BG)
        btns.pack(fill=tk.X, padx=15, pady=15)
        tk.Button(btns, text="Apply Filter", font=(t.FONT, 9, "bold"), bg=t.PRIMARY, fg="white", relief="flat",
                  cursor="hand2", command=apply_filter).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        tk.Button(btns, text="Clear", font=(t.FONT, 9), bg=t.CHIP_BG, fg=t.TEXT, relief="flat",
                  cursor="hand2", command=clear_filter).pack(side=tk.LEFT, padx=(8, 0), ipady=5, ipadx=10)
        popup.bind("<Escape>", lambda e: popup.destroy())

    def build_venues_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        tk.Label(self.scrollable_frame, text="Manage Venues", font=(t.FONT, 22, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 5))

        add_box = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        add_box.pack(fill=tk.X, padx=30, pady=10)

        name_entry = tk.Entry(add_box, font=(t.FONT, 11), bg=t.CARD_BG, relief="solid", bd=1, width=25)
        name_entry.pack(side=tk.LEFT, ipady=5, padx=(0, 10))
        name_entry.insert(0, "Venue Name")
        name_entry.bind("<FocusIn>", lambda e: name_entry.delete(0, tk.END) if name_entry.get() == "Venue Name" else None)

        addr_entry = tk.Entry(add_box, font=(t.FONT, 11), bg=t.CARD_BG, relief="solid", bd=1, width=30)
        addr_entry.pack(side=tk.LEFT, ipady=5, padx=(0, 10))
        addr_entry.insert(0, "Address / Location")
        addr_entry.bind("<FocusIn>", lambda e: addr_entry.delete(0, tk.END) if addr_entry.get() == "Address / Location" else None)

        maps_row = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        maps_row.pack(fill=tk.X, padx=30, pady=(0, 5))
        maps_entry = tk.Entry(maps_row, font=(t.FONT, 11), bg=t.CARD_BG, relief="solid", bd=1, width=62)
        maps_entry.pack(side=tk.LEFT, ipady=5)
        maps_entry.insert(0, "Google Maps link (optional)")
        maps_entry.bind("<FocusIn>", lambda e: maps_entry.delete(0, tk.END) if maps_entry.get() == "Google Maps link (optional)" else None)
        tk.Label(maps_row, text="In Google Maps: Share > Copy link", font=(t.FONT, 9, "italic"), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT, padx=10)

        def handle_add_venue():
            name = name_entry.get().strip()
            addr = addr_entry.get().strip()
            if not name or name == "Venue Name" or not addr or addr == "Address / Location":
                messagebox.showerror("Error", "Please enter valid venue name and address.")
                return
            maps_url = maps_entry.get().strip()
            if maps_url == "Google Maps link (optional)":
                maps_url = ""
            result = create_venue(name, addr, self.email, maps_url)
            if not result.get("success", True):
                messagebox.showerror("Error", result.get("message", "The venue could not be saved."))
                return
            messagebox.showinfo("Success", "Venue added successfully!")
            self.build_venues_content()

        add_btn = tk.Button(add_box, text=f"{ic.emoji('plus')} Add Venue", font=(t.FONT, 10, "bold"), bg=t.PRIMARY, fg="white", relief="flat", command=handle_add_venue)
        add_btn.pack(side=tk.LEFT, ipadx=15, ipady=7)
        t.add_hover(add_btn, t.PRIMARY, t.PRIMARY_HOVER)

        venues = get_venues_by_vendor(self.email)
        list_frame = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        list_frame.pack(fill=tk.X, padx=30, pady=15)

        tk.Label(list_frame, text="Your Current Venues:", font=(t.FONT, 12, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", pady=(0, 10))

        if not venues:
            tk.Label(list_frame, text="No venues found.", font=(t.FONT, 10, "italic"), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w")
            return

        for v in venues:
            row = tk.Frame(list_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
            row.pack(fill=tk.X, pady=5, ipady=5, ipadx=10)

            tk.Label(row, text=f"{v['name']}  -  {v['address']}", font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(side=tk.LEFT, padx=10)

            if v.get("maps_url"):
                venue_label(row, "Open map", v["maps_url"], font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT).pack(side=tk.LEFT, padx=(0, 5))
            else:
                tk.Label(row, text="No map link", font=(t.FONT, 9, "italic"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT, padx=(0, 5))
            edit_link_btn = tk.Button(row, text=f"{ic.emoji('edit')} Edit link", font=(t.FONT, 9, "bold"), bg=t.CHIP_BG, fg=t.TEXT, relief="flat",
                                      cursor="hand2", command=lambda venue=v: self.open_maps_link_window(venue))
            edit_link_btn.pack(side=tk.LEFT, padx=5, ipadx=8, ipady=2)
            t.add_hover(edit_link_btn, t.CHIP_BG, t.CHIP_HOVER)

            def make_delete(vid):
                return lambda: self.handle_delete_venue(vid)

            del_btn = tk.Button(row, text=f"{ic.emoji('trash')} Delete", font=(t.FONT, 9, "bold"), bg="#e74c3c", fg="white", relief="flat", command=make_delete(v["id"]))
            del_btn.pack(side=tk.RIGHT, padx=10, ipadx=8, ipady=3)
            t.add_hover(del_btn, "#e74c3c", "#c0392b")

    def open_maps_link_window(self, venue):
        width, height = 500, 260
        win = tk.Toplevel(self.root)
        win.title("Google Maps link")
        win.configure(bg=t.CARD_BG)
        win.resizable(False, False)
        win.transient(self.root)

        win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (height // 2)
        win.geometry(f"{width}x{height}+{x}+{y}")
        try:
            win.grab_set()
        except tk.TclError:
            pass

        tk.Label(win, text=venue["name"], font=(t.FONT, 15, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=25, pady=(20, 2))
        tk.Label(win, text="Paste a link from Google Maps (Share > Copy link). Customers and staff can click the venue name to open it. Leave the box empty to remove the link.",
                 font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED, wraplength=450, justify="left").pack(anchor="w", padx=25, pady=(0, 12))

        link_entry = tk.Entry(win, font=(t.FONT, 10), bg=t.FIELD_BG, relief="solid", bd=1)
        link_entry.pack(fill=tk.X, padx=25, ipady=6)
        link_entry.insert(0, venue.get("maps_url") or "")
        link_entry.focus_set()

        def save():
            result = update_venue_maps_url(venue["id"], self.email, link_entry.get().strip())
            if result.get("success"):
                win.destroy()
                messagebox.showinfo("Saved", result.get("message", "Map link saved."))
                self.build_venues_content()
            else:
                messagebox.showerror("Cannot save", result.get("message", "Something went wrong."), parent=win)

        btn_row = tk.Frame(win, bg=t.CARD_BG)
        btn_row.pack(fill=tk.X, padx=25, pady=20)

        cancel_btn = tk.Button(btn_row, text="Cancel", font=(t.FONT, 10, "bold"), bg=t.CHIP_BG, fg=t.TEXT, relief="flat", cursor="hand2", command=win.destroy)
        cancel_btn.pack(side=tk.LEFT, ipadx=15, ipady=6)
        t.add_hover(cancel_btn, t.CHIP_BG, t.CHIP_HOVER)

        save_btn = tk.Button(btn_row, text="Save link", font=(t.FONT, 10, "bold"), bg=t.PRIMARY, fg="white", relief="flat", cursor="hand2", command=save)
        save_btn.pack(side=tk.RIGHT, ipadx=15, ipady=6)
        t.add_hover(save_btn, t.PRIMARY, t.PRIMARY_HOVER)

    def handle_delete_venue(self, venue_id):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this venue?"):
            if not delete_venue(venue_id):
                messagebox.showerror("Cannot delete", "This venue still has events. Delete or move those events first.")
                return
            messagebox.showinfo("Deleted", "Venue deleted successfully.")
            self.build_venues_content()

    def build_categories_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        tk.Label(self.scrollable_frame, text="Manage Categories", font=(t.FONT, 22, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 5))

        add_box = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        add_box.pack(fill=tk.X, padx=30, pady=10)

        cat_entry = tk.Entry(add_box, font=(t.FONT, 11), bg=t.CARD_BG, relief="solid", bd=1, width=30)
        cat_entry.pack(side=tk.LEFT, ipady=5, padx=(0, 10))
        cat_entry.insert(0, "New Category Name")
        cat_entry.bind("<FocusIn>", lambda e: cat_entry.delete(0, tk.END) if cat_entry.get() == "New Category Name" else None)

        def handle_add_category():
            name = cat_entry.get().strip()
            if not name or name == "New Category Name":
                messagebox.showerror("Error", "Please enter a valid category name.")
                return
            if not add_vendor_category(self.email, name):
                messagebox.showerror("Error", "You already have a category with this name.")
                return
            messagebox.showinfo("Success", "Category added successfully!")
            self.build_categories_content()

        add_btn = tk.Button(add_box, text=f"{ic.emoji('plus')} Add Category", font=(t.FONT, 10, "bold"), bg=t.PRIMARY, fg="white", relief="flat", command=handle_add_category)
        add_btn.pack(side=tk.LEFT, ipadx=15, ipady=7)
        t.add_hover(add_btn, t.PRIMARY, t.PRIMARY_HOVER)

        categories = get_vendor_categories(self.email)
        list_frame = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        list_frame.pack(fill=tk.X, padx=30, pady=15)

        tk.Label(list_frame, text="Your Current Categories:", font=(t.FONT, 12, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", pady=(0, 10))

        if not categories:
            tk.Label(list_frame, text="No custom categories found.", font=(t.FONT, 10, "italic"), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w")
            return

        for cat in categories:
            row = tk.Frame(list_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
            row.pack(fill=tk.X, pady=5, ipady=5, ipadx=10)

            tk.Label(row, text=cat["name"], font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(side=tk.LEFT, padx=10)

            def make_delete(cid):
                return lambda: self.handle_delete_category(cid)

            del_btn = tk.Button(row, text=f"{ic.emoji('trash')} Delete", font=(t.FONT, 9, "bold"), bg="#e74c3c", fg="white", relief="flat", command=make_delete(cat["id"]))
            del_btn.pack(side=tk.RIGHT, padx=10, ipadx=8, ipady=3)
            t.add_hover(del_btn, "#e74c3c", "#c0392b")

    def handle_delete_category(self, cat_id):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this category?"):
            delete_vendor_category(cat_id)
            messagebox.showinfo("Deleted", "Category deleted successfully.")
            self.build_categories_content()

    def open_add_event_modal(self):
        self.open_event_form("Create New Event", None)

    def open_edit_event_modal(self, event):
        self.open_event_form("Edit Event Listing", event)

    def open_event_form(self, window_title, event=None):
        modal = tk.Toplevel(self.root)
        modal.title(window_title)
        modal.geometry("480x840")
        modal.configure(bg=t.CARD_BG)
        modal.resizable(False, False)

        modal.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (480 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (840 // 2)
        modal.geometry(f"+{x}+{y}")

        tk.Label(modal, text=window_title, font=(t.FONT, 18, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 10))

        form_frame = tk.Frame(modal, bg=t.CARD_BG)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30)

        # Title
        tk.Label(form_frame, text="EVENT TITLE", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(5, 2))
        title_entry = tk.Entry(form_frame, font=(t.FONT, 11), bg=t.FIELD_BG, relief="solid", bd=1)
        title_entry.pack(fill=tk.X, ipady=4)
        if event: title_entry.insert(0, event["title"])

        # Category Dropdown
        tk.Label(form_frame, text="CATEGORY", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(8, 2))
        vendor_cats = get_vendor_categories(self.email)
        cat_names = [c["name"] for c in vendor_cats] if vendor_cats else ["General"]
        
        selected_category = tk.StringVar(modal)
        if event and event["category"] in cat_names:
            selected_category.set(event["category"])
        else:
            selected_category.set(cat_names[0])

        cat_menu = tk.OptionMenu(form_frame, selected_category, *cat_names)
        cat_menu.config(font=(t.FONT, 10), bg=t.FIELD_BG, relief="solid", bd=1, highlightthickness=0)
        cat_menu.pack(fill=tk.X, ipady=2)

        # Venue Dropdown Selection
        tk.Label(form_frame, text="VENUE", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(8, 2))
        
        venues = get_venues_by_vendor(self.email)
        venue_dict = {f"{v['name']} ({v['address']})": v['id'] for v in venues} if venues else {}
        if venue_dict:
            venue_options = list(venue_dict.keys())
        else:
            venue_options = ["No venues available. Please add one in Manage Venues."]

        selected_venue_str = tk.StringVar(modal)
        if event and event.get("venue_id"):
            for v_name, v_id in venue_dict.items():
                if v_id == event["venue_id"]:
                    selected_venue_str.set(v_name)
                    break
        if not selected_venue_str.get() and venue_options:
            selected_venue_str.set(venue_options[0])

        venue_menu = tk.OptionMenu(form_frame, selected_venue_str, *venue_options)
        venue_menu.config(font=(t.FONT, 10), bg=t.FIELD_BG, relief="solid", bd=1, highlightthickness=0)
        venue_menu.pack(fill=tk.X, ipady=2)

        # Date & Time
        tk.Label(form_frame, text="DATE & TIME (YYYY-MM-DD HH:MM)", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(8, 2))
        datetime_entry = tk.Entry(form_frame, font=(t.FONT, 11), bg=t.FIELD_BG, relief="solid", bd=1)
        datetime_entry.pack(fill=tk.X, ipady=4)
        if event: datetime_entry.insert(0, event.get("event_datetime", ""))

        # Recurring or One-Time
        tk.Label(form_frame, text="EVENT TYPE", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(8, 2))
        recurring_var = tk.StringVar(modal)
        recurring_var.set(event.get("is_recurring", "One-Time") if event else "One-Time")
        
        rec_frame = tk.Frame(form_frame, bg=t.CARD_BG)
        rec_frame.pack(fill=tk.X)
        tk.Radiobutton(rec_frame, text="One-Time", variable=recurring_var, value="One-Time", bg=t.CARD_BG, font=(t.FONT, 9)).pack(side=tk.LEFT, padx=(0, 15))
        tk.Radiobutton(rec_frame, text="Recurring", variable=recurring_var, value="Recurring", bg=t.CARD_BG, font=(t.FONT, 9)).pack(side=tk.LEFT)

        # Visual Day Selection Boxes
        tk.Label(form_frame, text="RECURRENCE DAYS", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(8, 2))
        days_frame = tk.Frame(form_frame, bg=t.CARD_BG)
        days_frame.pack(fill=tk.X, pady=2)

        days_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        selected_days_set = set()
        if event and event.get("recur_day"):
            selected_days_set = set([d.strip() for d in event["recur_day"].split(",") if d.strip()])

        day_buttons = {}

        def update_day_buttons():
            for d_name, btn in day_buttons.items():
                if d_name in selected_days_set:
                    btn.config(bg=t.PRIMARY, fg="white")
                else:
                    btn.config(bg=t.CHIP_BG, fg=t.TEXT_MUTED)

        def toggle_day(d_name):
            if d_name in selected_days_set:
                selected_days_set.remove(d_name)
            else:
                selected_days_set.add(d_name)
            update_day_buttons()

        def deselect_day(d_name):
            if d_name in selected_days_set:
                selected_days_set.remove(d_name)
            update_day_buttons()

        for d in days_list:
            short_name = d[:3]
            btn = tk.Button(days_frame, text=short_name, font=(t.FONT, 9, "bold"), width=5, relief="flat")
            btn.pack(side=tk.LEFT, padx=2)
            btn.bind("<Button-1>", lambda e, name=d: toggle_day(name))
            btn.bind("<Double-Button-1>", lambda e, name=d: deselect_day(name))
            day_buttons[d] = btn

        update_day_buttons()

        # Price and capacity share one row, so the form keeps its height
        price_cap_row = tk.Frame(form_frame, bg=t.CARD_BG)
        price_cap_row.pack(fill=tk.X, pady=(8, 0))

        price_col = tk.Frame(price_cap_row, bg=t.CARD_BG)
        price_col.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        tk.Label(price_col, text="PRICE (AED)", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(0, 2))
        price_entry = tk.Entry(price_col, font=(t.FONT, 11), bg=t.FIELD_BG, relief="solid", bd=1)
        price_entry.pack(fill=tk.X, ipady=4)
        if event:
            raw_price = str(event["price"]).replace(" AED", "").strip()
            price_entry.insert(0, raw_price)

        capacity_col = tk.Frame(price_cap_row, bg=t.CARD_BG)
        capacity_col.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(capacity_col, text="CAPACITY (GUESTS)", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(0, 2))
        capacity_entry = tk.Entry(capacity_col, font=(t.FONT, 11), bg=t.FIELD_BG, relief="solid", bd=1)
        capacity_entry.pack(fill=tk.X, ipady=4)
        capacity_entry.insert(0, str(event.get("capacity") or DEFAULT_EVENT_CAPACITY) if event else str(DEFAULT_EVENT_CAPACITY))

        # Picture (optional): shown on the right of the event card, cropped to fit, never stretched.
        pic_state = {"b64": None, "remove": False}
        tk.Label(form_frame, text=f"EVENT PICTURE (OPTIONAL)", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(8, 2))
        pic_row = tk.Frame(form_frame, bg=t.CARD_BG)
        pic_row.pack(fill=tk.X)
        had_picture = bool(event) and event_images.load_image(event["id"]) is not None
        pic_label = tk.Label(pic_row, text="Current picture kept" if had_picture else "No picture selected", font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED)

        def choose_picture():
            path = filedialog.askopenfilename(parent=modal, title="Choose event picture",
                                              filetypes=[("Pictures", "*.png *.jpg *.jpeg *.webp *.bmp *.gif"), ("All files", "*.*")])
            if not path:
                return
            try:
                pic_state["b64"] = event_images.encode_image_file(path)
            except Exception as exc:
                messagebox.showerror("Picture", f"This picture could not be used: {exc}", parent=modal)
                return
            pic_state["remove"] = False
            pic_label.config(text=os.path.basename(path))

        def remove_picture():
            pic_state["b64"] = None
            pic_state["remove"] = True
            pic_label.config(text="No picture selected")

        tk.Button(pic_row, text="Choose picture...", font=(t.FONT, 9, "bold"), bg=t.CHIP_BG, fg=t.TEXT, relief="flat", command=choose_picture).pack(side=tk.LEFT, ipadx=8, ipady=3)
        tk.Button(pic_row, text="Remove", font=(t.FONT, 9), bg=t.CHIP_BG, fg="#e74c3c", relief="flat", command=remove_picture).pack(side=tk.LEFT, padx=(6, 0), ipadx=6, ipady=3)
        pic_label.pack(side=tk.LEFT, padx=8)

        # Description
        tk.Label(form_frame, text="DESCRIPTION", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(8, 2))
        desc_text = tk.Text(form_frame, font=(t.FONT, 10), bg=t.FIELD_BG, relief="solid", bd=1, height=3, width=30)
        desc_text.pack(fill=tk.X)
        if event: desc_text.insert("1.0", event["desc"])

        def save_event(e=None):
            title = title_entry.get().strip()
            category = selected_category.get()
            selected_venue_name = selected_venue_str.get()
            event_datetime = datetime_entry.get().strip()
            is_recurring = recurring_var.get()
            recur_day = ", ".join([d for d in days_list if d in selected_days_set]) if selected_days_set else "None"
            price_val = price_entry.get().strip()
            capacity_val = capacity_entry.get().strip()
            desc = desc_text.get("1.0", tk.END).strip()

            if not title or len(title) < 3:
                messagebox.showerror("Error", "Title must be at least 3 characters long.", parent=modal)
                return
            if not selected_venue_name or selected_venue_name not in venue_dict:
                messagebox.showerror("Error", "Please select a valid venue from your Manage Venues list.", parent=modal)
                return
            if not (price_val.isascii() and price_val.isdigit()) or int(price_val) <= 0:
                messagebox.showerror("Error", "Price must contain numbers only.", parent=modal)
                return
            if not (capacity_val.isascii() and capacity_val.isdigit()) or not 1 <= int(capacity_val) <= MAX_EVENT_CAPACITY:
                messagebox.showerror("Error", f"Capacity must be a whole number from 1 to {MAX_EVENT_CAPACITY}.", parent=modal)
                return
            if not desc or len(desc) < 10:
                messagebox.showerror("Error", "Description must be at least 10 characters long.", parent=modal)
                return

            try:
                parsed_datetime = datetime.strptime(event_datetime, "%Y-%m-%d %H:%M")
            except ValueError:
                messagebox.showerror("Error", "Date and time must look like 2026-12-31 23:00 (YYYY-MM-DD HH:MM).", parent=modal)
                return
            if is_recurring == "Recurring" and not selected_days_set:
                messagebox.showerror("Error", "Pick at least one recurrence day for a recurring event.", parent=modal)
                return
            if is_recurring != "Recurring":
                recur_day = "N/A"

            venue_id = venue_dict[selected_venue_name]
            formatted_price = f"{price_val} AED"
            recur_time = parsed_datetime.strftime("%H:%M")

            if event:
                res = update_event(event["id"], title, category, formatted_price, desc, venue_id, event_datetime, is_recurring, recur_day, recur_time,
                                   capacity=int(capacity_val), image_b64=pic_state["b64"], remove_image=pic_state["remove"])
                if not res.get("success", False):
                    messagebox.showerror("Error", res.get("message", "The event could not be saved."), parent=modal)
                    return
                event_images.forget(event["id"])
                messagebox.showinfo("Success", "Event updated successfully!", parent=modal)
            else:
                res = create_event(title, category, formatted_price, desc, self.email, venue_id, event_datetime, is_recurring, recur_day, recur_time,
                                   capacity=int(capacity_val), image_b64=pic_state["b64"])
                if not res.get("success", False):
                    messagebox.showerror("Error", res.get("message", "The event could not be saved."), parent=modal)
                    return
                messagebox.showinfo("Success", "Event created successfully!", parent=modal)

            modal.destroy()
            self.build_vendor_content()

        modal.bind("<Return>", save_event)

        # Enter inside the description box must add a new line, not save the form.
        def newline_in_description(event):
            desc_text.insert(tk.INSERT, "\n")
            return "break"

        desc_text.bind("<Return>", newline_in_description)

        save_btn = tk.Button(modal, text=f"Save", font=(t.FONT, 11, "bold"), bg=t.PRIMARY, fg="white", relief="flat", command=save_event)
        save_btn.pack(fill=tk.X, padx=30, pady=15, ipady=8)
        t.add_hover(save_btn, t.PRIMARY, t.PRIMARY_HOVER)

    def handle_delete(self, event_id):
        active = count_active_bookings(event_id)
        warning = f"\n\n{active} upcoming booking(s) will be cancelled with a full refund, and their tickets will stop working." if active else ""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this event listing?" + warning):
            delete_event(event_id)
            messagebox.showinfo("Deleted", "Event listing deleted successfully.")
            self.build_vendor_content()


def show_vendor_welcome(root, email):
    VendorWelcomeScreen(root, email)