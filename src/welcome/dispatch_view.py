import tkinter as tk
from tkinter import messagebox, ttk
import theme as t
import icons as ic
from digit_boxes import DigitBoxes
from database import get_all_vehicles, get_all_events, dispatch_vehicle_combination, free_vehicle, get_assigned_vehicles_for_event as _api_assigned_vehicles, get_event_demand, get_event_capacity, get_vehicle_types

from .table_style import (GEAR, CHECKED, UNCHECKED, ROW_EVEN, ROW_ODD, ROW_SELECTED, TABLE_STYLE,
                          style_tables, heading_text, stripe_tags, build_count_table)
from .cancellation import page_header

ANY_TYPE = "Any vehicle type"
ANY_LOCATION = "Any location"

# columns of the tables: (key, heading, width, anchor, can filter)
AVAILABLE_COLUMNS = [
    ("select", CHECKED, 50, "center", False),
    ("license", "License Number", 130, "center", True),
    ("type", "Vehicle Type", 200, "w", True),
    ("seats", "Seats", 80, "center", True),
    ("location", "Location", 180, "w", True),
]
ASSIGNED_COLUMNS = [
    ("select", CHECKED, 50, "center", False),
    ("license", "License Number", 130, "center", True),
    ("type", "Vehicle Type", 200, "w", True),
    ("seats", "Seats", 80, "center", True),
    ("location", "Location", 180, "w", True),
    ("reassign", "Next Recurring Event", 160, "center", True),
]


# the Event Dispatch page of the dispatcher
class DispatchView:
    def __init__(self, parent_screen):
        self.parent = parent_screen
        self.root = parent_screen.root
        self.email = parent_screen.email
        self.scrollable_frame = parent_screen.scrollable_frame

        self.current_event_key = None
        # the table of free vehicles only shows after the dispatcher picks the filters and presses Show
        self.search = None
        # None until a radio is picked, 0 = dont reassign, 1 = reassign for the next recurring event
        self.reassign_choice = None

        # for each table: the selected vehicle ids, the values hidden by a column filter and the license filter
        # we save the hidden values (not the allowed ones) so a new type or location shows by default
        self.selected = {"available": set(), "assigned": set()}
        self.hidden = {"available": {}, "assigned": {}}
        self.license_filter = {"available": "", "assigned": ""}

    # Helpers

    def get_assigned_vehicles_for_event(self, event_id):
        return _api_assigned_vehicles(event_id)

    def _get_val_for_col(self, v, col_key):
        if col_key == "license":
            return v['license_number']
        elif col_key == "type":
            return v['vehicle_type']
        elif col_key == "seats":
            return v.get('capacity', "")
        elif col_key == "location":
            return v['location']
        elif col_key == "reassign":
            if v.get('auto_reassign_recurring', 0):
                return "Reassign"
            return "Do not reassign"
        return ""

    def _passes_filters(self, table, v):
        lic = self.license_filter[table]
        if lic and str(v['license_number']).strip() != lic:
            return False
        for col_key in self.hidden[table]:
            hidden_vals = self.hidden[table][col_key]
            if str(self._get_val_for_col(v, col_key)) in hidden_vals:
                return False
        return True

    def _filter_active(self, table, col_key):
        if col_key == "license":
            return bool(self.license_filter[table])
        return bool(self.hidden[table].get(col_key))

    # like "2 x desert buggy, 1 x mini-yacht"
    def _type_breakdown(self, vehicles):
        counts = {}
        for v in vehicles:
            vt = v['vehicle_type']
            if vt in counts:
                counts[vt] += 1
            else:
                counts[vt] = 1
        types = []
        for vt in counts:
            types.append(vt)
        types.sort()
        text = ""
        for vt in types:
            if text != "":
                text = text + ", "
            text = text + str(counts[vt]) + " x " + str(vt)
        return text

    def _section_title(self, text, subtitle=None):
        tk.Label(self.scrollable_frame, text=text, font=(t.FONT, 13, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 2))
        if subtitle:
            tk.Label(self.scrollable_frame, text=subtitle, font=(t.FONT, 9), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 5))

    # ====== The page ======
    def build_dispatch_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        style_tables()

        page_header(self.scrollable_frame, "Event Dispatch Panel", self.build_dispatch_content)

        events = get_all_events()
        if not events:
            tk.Label(self.scrollable_frame, text="No events scheduled in system.", font=(t.FONT, 10, "italic"), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30)
            return

        # Step 1: the event
        sel_card = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
        sel_card.pack(fill=tk.X, padx=30, pady=10, ipady=10, ipadx=15)

        tk.Label(sel_card, text="1. SELECT EVENT", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.PRIMARY).pack(anchor="w", padx=10, pady=(5, 5))

        event_dict = {}
        event_options = []
        for e in events:
            key = str(e['title']) + " | " + str(e['event_datetime']) + " | " + str(e['is_recurring'])
            if key not in event_dict:
                event_options.append(key)
            event_dict[key] = e

        selected_event_str = tk.StringVar(sel_card)
        # keep the same event when the page is drawn again
        if self.current_event_key in event_dict:
            selected_event_str.set(self.current_event_key)
        else:
            selected_event_str.set(event_options[0])
            self.current_event_key = event_options[0]

        def on_event_change(*args):
            self.current_event_key = selected_event_str.get()
            self.selected["available"].clear()
            self.selected["assigned"].clear()
            self.reassign_choice = None
            self.build_dispatch_content()

        selected_event_str.trace_add("write", on_event_change)

        event_menu = tk.OptionMenu(sel_card, selected_event_str, *event_options)
        event_menu.config(font=(t.FONT, 10), bg=t.FIELD_BG, anchor="w")
        event_menu.pack(fill=tk.X, padx=10, pady=5)

        current_event = event_dict[selected_event_str.get()]
        current_event_id = current_event['id']
        bookings_count, guests_count = get_event_demand(current_event_id)
        event_capacity = get_event_capacity(current_event_id)
        if event_capacity["source"] == "vehicles":
            capacity_note = "total seats of the assigned vehicles"
        else:
            capacity_note = "set by the vendor, no vehicles assigned"

        stats = tk.Frame(sel_card, bg=t.CARD_BG)
        stats.pack(fill=tk.X, padx=10, pady=(5, 0))
        capacity_text = str(event_capacity['total']) + " (" + capacity_note + ")"
        for label, value in [("Upcoming bookings", bookings_count), ("Guests booked", guests_count),
                             ("Capacity per date", capacity_text)]:
            box = tk.Frame(stats, bg=t.FIELD_BG, padx=12, pady=6)
            box.pack(side=tk.LEFT, padx=(0, 10))
            tk.Label(box, text=label, font=(t.FONT, 8, "bold"), bg=t.FIELD_BG, fg=t.TEXT_MUTED).pack(anchor="w")
            tk.Label(box, text=str(value), font=(t.FONT, 11, "bold"), bg=t.FIELD_BG, fg=t.TEXT).pack(anchor="w")

        seats_by_type = {}
        for vt in get_vehicle_types():
            seats_by_type[vt["name"]] = vt["capacity"]
        vehicles = get_all_vehicles(self.email)
        available_vehicles = []
        for v in vehicles:
            if v['status'] == 'Available':
                available_vehicles.append(v)
        assigned_vehicles = self.get_assigned_vehicles_for_event(current_event_id)
        for v in assigned_vehicles:
            if 'capacity' not in v:
                v['capacity'] = seats_by_type.get(v['vehicle_type'], 4)

        self._build_available_section(current_event, available_vehicles)
        self._build_assigned_section(assigned_vehicles)

    # ====== Step 2 and 3: find free vehicles and assign them ======
    def _build_available_section(self, current_event, available_vehicles):
        self._section_title("2. Find Available Vehicles")

        filter_card = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
        filter_card.pack(fill=tk.X, padx=30, pady=5, ipady=8, ipadx=10)

        if not available_vehicles:
            tk.Label(filter_card, text="No available vehicles in your fleet. Free or register vehicles first.",
                     font=(t.FONT, 10, "italic"), bg=t.CARD_BG, fg="#e74c3c").pack(anchor="w", padx=10, pady=5)
            return

        all_types = []
        all_locations = []
        for v in available_vehicles:
            if v['vehicle_type'] not in all_types:
                all_types.append(v['vehicle_type'])
            if v['location'] not in all_locations:
                all_locations.append(v['location'])
        all_types.sort()
        all_locations.sort()
        type_options = [ANY_TYPE] + all_types
        location_options = [ANY_LOCATION] + all_locations

        search = self.search
        if not search:
            search = {}
        if search.get("type") in type_options:
            start_type = search.get("type")
        else:
            start_type = ANY_TYPE
        if search.get("location") in location_options:
            start_location = search.get("location")
        else:
            start_location = ANY_LOCATION
        type_var = tk.StringVar(filter_card, value=start_type)
        location_var = tk.StringVar(filter_card, value=start_location)

        row = tk.Frame(filter_card, bg=t.CARD_BG)
        row.pack(fill=tk.X, padx=10, pady=5)
        for label, var, options in [("Vehicle type", type_var, type_options), ("Location", location_var, location_options)]:
            col = tk.Frame(row, bg=t.CARD_BG)
            col.pack(side=tk.LEFT, padx=(0, 15))
            tk.Label(col, text=label, font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w")
            menu = tk.OptionMenu(col, var, *options)
            menu.config(font=(t.FONT, 10), bg=t.FIELD_BG, width=24, anchor="w")
            menu.pack(anchor="w", pady=(2, 0))

        def show_vehicles():
            self.search = {"type": type_var.get(), "location": location_var.get()}
            self.selected["available"].clear()
            self.build_dispatch_content()

        show_btn = tk.Button(row, text="Show available vehicles", font=(t.FONT, 10, "bold"), bg=t.PRIMARY, fg="white",
                             relief="flat", cursor="hand2", command=show_vehicles)
        show_btn.pack(side=tk.LEFT, anchor="s", ipadx=10, ipady=4)
        t.add_hover(show_btn, t.PRIMARY, t.PRIMARY_HOVER)

        if self.search is None:
            tk.Label(filter_card, text=str(len(available_vehicles)) + " vehicles are free: " + self._type_breakdown(available_vehicles) + ".",
                     font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=10, pady=(4, 0))
            return

        matches = []
        for v in available_vehicles:
            type_ok = self.search["type"] == ANY_TYPE or v['vehicle_type'] == self.search["type"]
            location_ok = self.search["location"] == ANY_LOCATION or v['location'] == self.search["location"]
            if type_ok and location_ok:
                matches.append(v)

        # take out selected vehicles that are not in the result anymore
        match_ids = set()
        for v in matches:
            match_ids.add(v['id'])
        for vid in list(self.selected["available"]):
            if vid not in match_ids:
                self.selected["available"].remove(vid)

        if not matches:
            tk.Label(self.scrollable_frame, text="No free vehicles match these filters. Try another type or location.",
                     font=(t.FONT, 10, "italic"), bg=t.PAGE_BG, fg="#e74c3c").pack(anchor="w", padx=30, pady=8)
            return

        visible = []
        for v in matches:
            if self._passes_filters("available", v):
                visible.append(v)
        tk.Label(self.scrollable_frame, text=str(len(matches)) + " vehicles found",
                 font=(t.FONT, 10, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(10, 4))
        match_types = []
        for v in matches:
            match_types.append(v['vehicle_type'])
        build_count_table(self.scrollable_frame, match_types).pack(anchor="w", padx=30, pady=(0, 10))


        summary_var = tk.StringVar()

        def on_available_change():
            refresh_summary()

        tree = self._build_table("available", AVAILABLE_COLUMNS, matches, visible, on_select_change=on_available_change)

        # quick select: a number of vehicles of the same type at once
        quick = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        quick.pack(fill=tk.X, padx=30, pady=(6, 0))
        visible_types = []
        for v in visible:
            if v['vehicle_type'] not in visible_types:
                visible_types.append(v['vehicle_type'])
        visible_types.sort()
        if visible_types:
            tk.Label(quick, text="Quick select", font=(t.FONT, 9, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(side=tk.LEFT)
            qty_var = tk.IntVar(quick, value=1)
            qty_type_var = tk.StringVar(quick, value=visible_types[0])
            qty_spin = tk.Spinbox(quick, from_=1, to=len(visible), width=4, textvariable=qty_var, font=(t.FONT, 10), state="readonly")
            qty_spin.pack(side=tk.LEFT, padx=6)
            tk.Label(quick, text="x", font=(t.FONT, 9), bg=t.PAGE_BG, fg=t.TEXT).pack(side=tk.LEFT)
            qty_menu = tk.OptionMenu(quick, qty_type_var, *visible_types)
            qty_menu.config(font=(t.FONT, 9), bg=t.FIELD_BG)
            qty_menu.pack(side=tk.LEFT, padx=6)

            def quick_select():
                same_type = []
                for v in visible:
                    if v['vehicle_type'] == qty_type_var.get():
                        same_type.append(v['id'])
                wanted = qty_var.get()
                if wanted > len(same_type):
                    messagebox.showwarning("Not enough vehicles", "Only " + str(len(same_type)) + " x " + qty_type_var.get() + " are free with these filters.")
                    wanted = len(same_type)
                # change the selection only for this type, the other types stay the same
                for vid in same_type:
                    self.selected["available"].discard(vid)
                for vid in same_type[:wanted]:
                    self.selected["available"].add(vid)
                tree.refresh_rows()
                refresh_summary()

            def clear_selection():
                self.selected["available"].clear()
                tree.refresh_rows()
                refresh_summary()

            tk.Button(quick, text="Select", font=(t.FONT, 9, "bold"), bg=t.CHIP_BG, fg=t.TEXT, relief="flat",
                      cursor="hand2", command=quick_select).pack(side=tk.LEFT, ipadx=8)
            tk.Button(quick, text="Clear selection", font=(t.FONT, 9), bg=t.PAGE_BG, fg=t.TEXT_MUTED, relief="flat",
                      cursor="hand2", command=clear_selection).pack(side=tk.LEFT, padx=6)

        # Step 3: reassign choice and the assign button
        self._section_title("3. Assign to Event")
        assign_card = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
        assign_card.pack(fill=tk.X, padx=30, pady=5, ipady=8, ipadx=10)

        tk.Label(assign_card, textvariable=summary_var, font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.TEXT,
                 justify="left", wraplength=700).pack(anchor="w", padx=10, pady=(5, 8))

        tk.Label(assign_card, text="After this event, should these vehicles move on to the next recurring event? (required)",
                 font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=10)
        if self.reassign_choice is None:
            start_choice = -1
        else:
            start_choice = self.reassign_choice
        reassign_var = tk.IntVar(assign_card, value=start_choice)

        def on_reassign_pick():
            self.reassign_choice = reassign_var.get()
            refresh_summary()

        for value, text in [(0, "Do not reassign vehicle"), (1, "Reassign vehicle for next recurring event")]:
            tk.Radiobutton(assign_card, text=text, variable=reassign_var, value=value, command=on_reassign_pick,
                           font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT, activebackground=t.CARD_BG,
                           selectcolor=t.CARD_BG, cursor="hand2").pack(anchor="w", padx=20)
        if current_event.get('is_recurring') != "Recurring":
            tk.Label(assign_card, text="This is a one-time event, so reassigning only matters if it is made recurring later.",
                     font=(t.FONT, 8, "italic"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=20)

        hint_label = tk.Label(assign_card, text="", font=(t.FONT, 9), bg=t.CARD_BG, fg="#e74c3c")

        def handle_assign_vehicles():
            if not self.selected["available"] or self.reassign_choice is None:
                return
            available_ids = set()
            for v in matches:
                available_ids.add(v['id'])
            assignments = []
            for vid in self.selected["available"]:
                if vid in available_ids:
                    assignments.append({"vehicle_id": vid, "auto_reassign_recurring": self.reassign_choice})
            assigned_count = dispatch_vehicle_combination(current_event['id'], assignments)
            if assigned_count < len(assignments):
                messagebox.showwarning("Partly assigned", "Assigned " + str(assigned_count) + " of " + str(len(assignments)) + " vehicles. The others were taken in the meantime.")
            else:
                messagebox.showinfo("Success", "Assigned " + str(assigned_count) + " vehicles to the event.")
            self.selected["available"].clear()
            self.reassign_choice = None
            self.build_dispatch_content()

        assign_btn = tk.Button(assign_card, text=ic.emoji("plus") + " Assign Selected Vehicles", font=(t.FONT, 10, "bold"),
                               fg="white", relief="flat", command=handle_assign_vehicles)
        assign_btn.pack(anchor="w", padx=10, pady=(10, 2), ipadx=12, ipady=6)
        hint_label.pack(anchor="w", padx=10, pady=(0, 4))

        def refresh_summary():
            chosen = []
            for v in matches:
                if v['id'] in self.selected["available"]:
                    chosen.append(v)
            if chosen:
                # total seats of the chosen vehicles
                seats = 0
                for v in chosen:
                    seats = seats + int(v.get('capacity') or 0)
                summary_var.set("Selected: " + str(len(chosen)) + " vehicles (" + self._type_breakdown(chosen) + "), " + str(seats) + " seats")
            else:
                summary_var.set("Selected: no vehicles yet")

            missing = []
            if not chosen:
                missing.append("select at least one vehicle")
            if self.reassign_choice is None:
                missing.append("choose a reassign option")
            if missing:
                assign_btn.config(state=tk.DISABLED, bg="#bdc3c7", cursor="arrow")
                assign_btn.unbind("<Enter>")
                assign_btn.unbind("<Leave>")
                hint_label.config(text="To assign, " + " and ".join(missing) + ".")
            else:
                assign_btn.config(state=tk.NORMAL, bg=t.ACCENT, cursor="hand2")
                t.add_hover(assign_btn, t.ACCENT, "#e67e22")
                hint_label.config(text="")

        refresh_summary()

    # ====== Step 4: the vehicles that are already on this event ======
    def _build_assigned_section(self, assigned_vehicles):
        self._section_title("Assigned Vehicles for This Event")

        if not assigned_vehicles:
            tk.Label(self.scrollable_frame, text="No vehicles currently assigned to this event.", font=(t.FONT, 10, "italic"), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=5)
            return

        assigned_ids = set()
        for v in assigned_vehicles:
            assigned_ids.add(v['id'])
        for vid in list(self.selected["assigned"]):
            if vid not in assigned_ids:
                self.selected["assigned"].remove(vid)
        seats = 0
        for v in assigned_vehicles:
            seats = seats + int(v.get('capacity') or 0)
        tk.Label(self.scrollable_frame, text=str(len(assigned_vehicles)) + " vehicles, " + str(seats) + " seats",
                 font=(t.FONT, 10, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(0, 4))
        assigned_types = []
        for v in assigned_vehicles:
            assigned_types.append(v['vehicle_type'])
        build_count_table(self.scrollable_frame, assigned_types).pack(anchor="w", padx=30, pady=(0, 10))

        visible = []
        for v in assigned_vehicles:
            if self._passes_filters("assigned", v):
                visible.append(v)
        btn_frame = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)

        def refresh_button():
            n = len(self.selected["assigned"])
            if n:
                unassign_btn.config(text=ic.emoji("cross") + " Unassign Selected Vehicles (" + str(n) + ")",
                                    state=tk.NORMAL, bg="#e74c3c")
            else:
                unassign_btn.config(text=ic.emoji("cross") + " Unassign Selected Vehicles (" + str(n) + ")",
                                    state=tk.DISABLED, bg="#bdc3c7")

        def on_assigned_change():
            refresh_button()

        self._build_table("assigned", ASSIGNED_COLUMNS, assigned_vehicles, visible, on_select_change=on_assigned_change)
        btn_frame.pack(fill=tk.X, padx=30, pady=(6, 20))

        def handle_unassign_vehicles():
            ids = list(self.selected["assigned"])
            if not ids:
                return
            if not messagebox.askyesno("Unassign vehicles", "Send " + str(len(ids)) + " vehicles back to the available fleet?"):
                return
            for vid in ids:
                free_vehicle(vid)
            self.selected["assigned"].clear()
            self.build_dispatch_content()

        unassign_btn = tk.Button(btn_frame, font=(t.FONT, 10, "bold"), fg="white", relief="flat", cursor="hand2", command=handle_unassign_vehicles)
        unassign_btn.pack(side=tk.LEFT, ipadx=12, ipady=6)
        refresh_button()

    # ====== table used by both sections ======
    def _build_table(self, table, columns, all_rows, visible_rows, on_select_change):
        frame = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
        frame.pack(fill=tk.X, padx=30, pady=2)

        col_keys = []
        for c in columns:
            col_keys.append(c[0])
        # between 3 and 8 rows high
        rows_high = len(visible_rows)
        if rows_high < 3:
            rows_high = 3
        if rows_high > 8:
            rows_high = 8
        tree = ttk.Treeview(frame, columns=col_keys, show="headings", height=rows_high,
                            style=TABLE_STYLE, selectmode="none")
        stripe_tags(tree)

        selected = self.selected[table]
        visible_ids = []
        for v in visible_rows:
            visible_ids.append(v['id'])

        # if all the visible rows are picked it unpicks them, otherwise it picks all of them
        def toggle_all():
            all_picked = True
            for vid in visible_ids:
                if vid not in selected:
                    all_picked = False
            if visible_ids and all_picked:
                for vid in visible_ids:
                    selected.discard(vid)
            else:
                for vid in visible_ids:
                    selected.add(vid)
            refresh_rows()
            on_select_change()

        for col_key, heading, width, anchor, filterable in columns:
            if col_key == "select":
                tree.heading(col_key, text=heading, command=toggle_all)
            elif filterable:
                def open_filter(ck=col_key, h=heading):
                    self._open_filter_window(table, ck, h, all_rows)
                tree.heading(col_key, text=heading_text(heading, self._filter_active(table, col_key)), anchor=anchor,
                             command=open_filter)
            else:
                tree.heading(col_key, text=heading)
            if col_key == "select" or col_key == "seats":
                stretch = False
            else:
                stretch = True
            tree.column(col_key, width=width, minwidth=width, anchor=anchor, stretch=stretch)

        def refresh_rows():
            i = 0
            for item in tree.get_children():
                vid = int(item)
                vals = list(tree.item(item, "values"))
                if vid in selected:
                    vals[0] = CHECKED
                    tag = "picked"
                else:
                    vals[0] = UNCHECKED
                    if i % 2:
                        tag = "odd"
                    else:
                        tag = "even"
                tree.item(item, values=vals, tags=(tag,))
                i += 1

        for v in visible_rows:
            values = [UNCHECKED]
            for ck in col_keys[1:]:
                values.append(self._get_val_for_col(v, ck))
            tree.insert("", tk.END, iid=str(v['id']), values=values)
        refresh_rows()

        def on_click(event):
            if tree.identify("region", event.x, event.y) not in ("cell", "tree"):
                return
            item = tree.identify_row(event.y)
            if not item:
                return
            vid = int(item)
            if vid in selected:
                selected.discard(vid)
            else:
                selected.add(vid)
            refresh_rows()
            on_select_change()

        tree.bind("<Button-1>", on_click)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        if not visible_rows:
            tk.Label(self.scrollable_frame, text="All rows are hidden by your column filters. Click a " + GEAR + " heading to change them.",
                     font=(t.FONT, 9, "italic"), bg=t.PAGE_BG, fg="#e74c3c").pack(anchor="w", padx=30)

        tree.refresh_rows = refresh_rows
        return tree

    def _open_filter_window(self, table, col_key, col_name, rows):
        popup = tk.Toplevel(self.root)
        popup.title("Filter: " + col_name)
        popup.configure(bg=t.CARD_BG)
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()

        tk.Label(popup, text=GEAR + " Filter " + col_name, font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=15, pady=(15, 10))

        if col_key == "license":
            tk.Label(popup, text="Show only this license number", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15)
            lic_boxes = DigitBoxes(popup, groups=1, group_size=5, font_size=12, initial=self.license_filter[table])
            lic_boxes.pack(anchor="w", padx=15, pady=6)
            lic_boxes.focus_first()
            tk.Label(popup, text="Leave empty to show all licenses.", font=(t.FONT, 8), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15)

            def apply_filter(event=None):
                if lic_boxes.get() and not lic_boxes.is_complete():
                    lic_boxes.set_error(True)
                    return
                self.license_filter[table] = lic_boxes.get()
                popup.destroy()
                self.build_dispatch_content()

            def clear_filter():
                self.license_filter[table] = ""
                popup.destroy()
                self.build_dispatch_content()

            lic_boxes.bind_all_boxes("<Return>", apply_filter)
        else:
            # all the different values with how many times each one is there
            val_set = set()
            counts = {}
            for v in rows:
                val = str(self._get_val_for_col(v, col_key))
                val_set.add(val)
                if val in counts:
                    counts[val] += 1
                else:
                    counts[val] = 1

            # sort: numbers first (by value) then the text (not case sensitive), insertion sort
            unique_vals = []
            for val in val_set:
                unique_vals.append(val)
            for i in range(1, len(unique_vals)):
                temp = unique_vals[i]
                if temp.isdigit():
                    temp_key = (0, int(temp))
                else:
                    temp_key = (1, temp.lower())
                j = i - 1
                while j >= 0:
                    if unique_vals[j].isdigit():
                        j_key = (0, int(unique_vals[j]))
                    else:
                        j_key = (1, unique_vals[j].lower())
                    if j_key > temp_key:
                        unique_vals[j + 1] = unique_vals[j]
                        j -= 1
                    else:
                        break
                unique_vals[j + 1] = temp

            hidden = self.hidden[table].get(col_key, set())
            var_dict = {}

            toggles = tk.Frame(popup, bg=t.CARD_BG)
            toggles.pack(fill=tk.X, padx=15)
            frame_chk = tk.Frame(popup, bg=t.CARD_BG)
            frame_chk.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
            for val in unique_vals:
                var = tk.BooleanVar(value=(val not in hidden))
                var_dict[val] = var
                tk.Checkbutton(frame_chk, text=val + "  (" + str(counts[val]) + ")", variable=var, bg=t.CARD_BG, font=(t.FONT, 9),
                               fg=t.TEXT, activebackground=t.CARD_BG, anchor="w").pack(fill=tk.X, pady=1)

            def select_all():
                for val in var_dict:
                    var_dict[val].set(True)

            def select_none():
                for val in var_dict:
                    var_dict[val].set(False)

            tk.Button(toggles, text="Select all", font=(t.FONT, 8), bg=t.CHIP_BG, fg=t.TEXT, relief="flat",
                      command=select_all).pack(side=tk.LEFT, padx=(0, 6))
            tk.Button(toggles, text="Select none", font=(t.FONT, 8), bg=t.CHIP_BG, fg=t.TEXT, relief="flat",
                      command=select_none).pack(side=tk.LEFT, padx=(0, 6))

            def apply_filter(event=None):
                hidden_now = set()
                for val in var_dict:
                    if not var_dict[val].get():
                        hidden_now.add(val)
                self.hidden[table][col_key] = hidden_now
                popup.destroy()
                self.build_dispatch_content()

            def clear_filter():
                if col_key in self.hidden[table]:
                    del self.hidden[table][col_key]
                popup.destroy()
                self.build_dispatch_content()

        btns = tk.Frame(popup, bg=t.CARD_BG)
        btns.pack(fill=tk.X, padx=15, pady=15)
        tk.Button(btns, text="Apply Filter", font=(t.FONT, 9, "bold"), bg=t.PRIMARY, fg="white", relief="flat",
                  cursor="hand2", command=apply_filter).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        tk.Button(btns, text="Clear", font=(t.FONT, 9), bg=t.CHIP_BG, fg=t.TEXT, relief="flat",
                  cursor="hand2", command=clear_filter).pack(side=tk.LEFT, padx=(8, 0), ipady=5, ipadx=10)

        def on_escape(event):
            popup.destroy()
        popup.bind("<Escape>", on_escape)
