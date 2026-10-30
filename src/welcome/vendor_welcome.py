from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from .users_welcome import BaseWelcomeScreen
from database import (
    get_events_by_vendor, create_event, update_event, delete_event,
    get_vendor_categories, add_vendor_category, delete_vendor_category,
    get_venues_by_vendor, create_venue, delete_venue
)
import theme as t


class VendorWelcomeScreen(BaseWelcomeScreen):
    def __init__(self, root, email):
        super().__init__(root, email, "Vendor")
        self.root = root

        self.add_nav_button("My Events", self.build_vendor_content)
        self.add_nav_button("Manage Venues", self.build_venues_content)
        self.add_nav_button("Manage Categories", self.build_categories_content)
        self.add_nav_button("Add New Event", self.open_add_event_modal)

        self.build_vendor_content()

    def build_vendor_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        tk.Label(self.scrollable_frame, text=f"Welcome back, {self.username}!", font=(t.FONT, 22, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 5))
        tk.Label(self.scrollable_frame, text="Manage your event listings below.", font=(t.FONT, 11), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 15))

        action_frame = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        action_frame.pack(fill=tk.X, padx=30, pady=10)
        
        add_btn = tk.Button(action_frame, text="+ Create New Event Listing", font=(t.FONT, 10, "bold"), bg=t.ACCENT, fg="white", relief="flat", command=self.open_add_event_modal)
        add_btn.pack(side=tk.LEFT, ipadx=15, ipady=8)
        t.add_hover(add_btn, t.ACCENT, "#e67e22")

        events = get_events_by_vendor(self.email)

        if not events:
            tk.Label(self.scrollable_frame, text="No event listings found. Create your first one above!", font=(t.FONT, 11, "italic"), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=20)
            return

        for event in events:
            card = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
            card.pack(fill=tk.X, padx=30, pady=10, ipady=10)

            top_row = tk.Frame(card, bg=t.CARD_BG)
            top_row.pack(fill=tk.X, padx=15, pady=5)
            tk.Label(top_row, text=f"Category: {event['category']}", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.PRIMARY).pack(side=tk.LEFT)
            tk.Label(top_row, text=event['price'], font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.ACCENT).pack(side=tk.RIGHT)

            tk.Label(card, text=event['title'], font=(t.FONT, 14, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=15, pady=2)
            venue_display = event.get('venue_name') or 'Unknown Venue'
            recur_suffix = f" ({event['recur_day']})" if event['is_recurring'] == "Recurring" and event['recur_day'] not in (None, "", "None", "N/A") else ""
            tk.Label(card, text=f"📍 {venue_display} | ⏰ {event['event_datetime']} | 🔁 {event['is_recurring']}{recur_suffix}", font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=2)
            tk.Label(card, text=event['desc'], font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED, wraplength=600, justify="left").pack(anchor="w", padx=15, pady=5)

            btn_row = tk.Frame(card, bg=t.CARD_BG)
            btn_row.pack(anchor="w", padx=15, pady=(5, 10))

            edit_btn = tk.Button(btn_row, text="Edit", bg=t.PRIMARY, fg="white", font=(t.FONT, 9, "bold"), relief="flat", command=lambda e=event: self.open_edit_event_modal(e))
            edit_btn.pack(side=tk.LEFT, padx=(0, 10), ipadx=10, ipady=4)
            t.add_hover(edit_btn, t.PRIMARY, t.PRIMARY_HOVER)

            delete_btn = tk.Button(btn_row, text="Delete", bg="#e74c3c", fg="white", font=(t.FONT, 9, "bold"), relief="flat", command=lambda eid=event['id']: self.handle_delete(eid))
            delete_btn.pack(side=tk.LEFT, ipadx=10, ipady=4)
            t.add_hover(delete_btn, "#e74c3c", "#c0392b")

    def build_venues_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        tk.Label(self.scrollable_frame, text="Manage Venues", font=(t.FONT, 22, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 5))
        tk.Label(self.scrollable_frame, text="Add or remove venues where you host events.", font=(t.FONT, 11), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 15))

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

        def handle_add_venue():
            name = name_entry.get().strip()
            addr = addr_entry.get().strip()
            if not name or name == "Venue Name" or not addr or addr == "Address / Location":
                messagebox.showerror("Error", "Please enter valid venue name and address.")
                return
            create_venue(name, addr, self.email)
            messagebox.showinfo("Success", "Venue added successfully!")
            self.build_venues_content()

        add_btn = tk.Button(add_box, text="Add Venue", font=(t.FONT, 10, "bold"), bg=t.PRIMARY, fg="white", relief="flat", command=handle_add_venue)
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

            tk.Label(row, text=f"{v['name']} — {v['address']}", font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(side=tk.LEFT, padx=10)

            def make_delete(vid):
                return lambda: self.handle_delete_venue(vid)

            del_btn = tk.Button(row, text="Delete", font=(t.FONT, 9, "bold"), bg="#e74c3c", fg="white", relief="flat", command=make_delete(v["id"]))
            del_btn.pack(side=tk.RIGHT, padx=10, ipadx=8, ipady=3)
            t.add_hover(del_btn, "#e74c3c", "#c0392b")

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
        tk.Label(self.scrollable_frame, text="Add or remove custom categories for your events.", font=(t.FONT, 11), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 15))

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

        add_btn = tk.Button(add_box, text="Add Category", font=(t.FONT, 10, "bold"), bg=t.PRIMARY, fg="white", relief="flat", command=handle_add_category)
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

            del_btn = tk.Button(row, text="Delete", font=(t.FONT, 9, "bold"), bg="#e74c3c", fg="white", relief="flat", command=make_delete(cat["id"]))
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
        modal.geometry("480x760")
        modal.configure(bg=t.CARD_BG)
        modal.resizable(False, False)

        modal.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (480 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (760 // 2)
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

        # Price
        tk.Label(form_frame, text="PRICE", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(8, 2))
        price_row = tk.Frame(form_frame, bg=t.CARD_BG)
        price_row.pack(fill=tk.X)
        price_entry = tk.Entry(price_row, font=(t.FONT, 11), bg=t.FIELD_BG, relief="solid", bd=1)
        price_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        if event:
            raw_price = str(event["price"]).replace(" AED", "").strip()
            price_entry.insert(0, raw_price)
        tk.Label(price_row, text="AED", font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(side=tk.LEFT, padx=(8, 0))

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
                update_event(event["id"], title, category, formatted_price, desc, venue_id, event_datetime, is_recurring, recur_day, recur_time)
                messagebox.showinfo("Success", "Event updated successfully!", parent=modal)
            else:
                create_event(title, category, formatted_price, desc, self.email, venue_id, event_datetime, is_recurring, recur_day, recur_time)
                messagebox.showinfo("Success", "Event created successfully!", parent=modal)

            modal.destroy()
            self.build_vendor_content()

        modal.bind("<Return>", save_event)

        # Enter inside the description box must add a new line, not save the form.
        def newline_in_description(event):
            desc_text.insert(tk.INSERT, "\n")
            return "break"

        desc_text.bind("<Return>", newline_in_description)

        save_btn = tk.Button(modal, text="Save Event", font=(t.FONT, 11, "bold"), bg=t.PRIMARY, fg="white", relief="flat", command=save_event)
        save_btn.pack(fill=tk.X, padx=30, pady=15, ipady=8)
        t.add_hover(save_btn, t.PRIMARY, t.PRIMARY_HOVER)

    def handle_delete(self, event_id):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this event listing?"):
            delete_event(event_id)
            messagebox.showinfo("Deleted", "Event listing deleted successfully.")
            self.build_vendor_content()


def show_vendor_welcome(root, email):
    VendorWelcomeScreen(root, email)