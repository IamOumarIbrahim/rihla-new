import tkinter as tk
from tkinter import messagebox, ttk
from collections import Counter
import theme as t
import icons as ic
from digit_boxes import DigitBoxes
from database import get_all_vehicles, get_all_events, dispatch_vehicle_combination, free_vehicle, get_assigned_vehicles_for_event as _api_assigned_vehicles, get_event_demand, get_event_capacity, get_vehicle_types

from .table_style import (GEAR, CHECKED, UNCHECKED, ROW_EVEN, ROW_ODD, ROW_SELECTED, TABLE_STYLE,
                          style_tables, heading_text, stripe_tags, build_count_table)
from .cancellation import page_header

ANY_TYPE = "Any vehicle type"
ANY_LOCATION = "Any location"

# Columns of each table: (key, heading, width, anchor, filterable)
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


class DispatchView:
    def __init__(self, parent_screen):
        self.parent = parent_screen
        self.root = parent_screen.root
        self.email = parent_screen.email
        self.scrollable_frame = parent_screen.scrollable_frame

        self.current_event_key = None
        # The available table only shows after the dispatcher picks filters and presses Show.
        self.search = None
        # None until the dispatcher picks a radio: 0 = do not reassign, 1 = reassign for the next recurring event
        self.reassign_choice = None

        # Per table: selected vehicle ids, values hidden by a column filter, and the license filter.
        # Hidden values (not allowed ones) are stored so a new vehicle type or location shows by default.
        self.selected = {"available": set(), "assigned": set()}
        self.hidden = {"available": {}, "assigned": {}}
        self.license_filter = {"available": "", "assigned": ""}

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
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
            return "Reassign" if v.get('auto_reassign_recurring', 0) else "Do not reassign"
        return ""

    def _passes_filters(self, table, v):
        lic = self.license_filter[table]
        if lic and str(v['license_number']).strip() != lic:
            return False
        for col_key, hidden_vals in self.hidden[table].items():
            if str(self._get_val_for_col(v, col_key)) in hidden_vals:
                return False
        return True

    def _filter_active(self, table, col_key):
        if col_key == "license":
            return bool(self.license_filter[table])
        return bool(self.hidden[table].get(col_key))

    @staticmethod
    def _type_breakdown(vehicles):
        counts = Counter(v['vehicle_type'] for v in vehicles)
        return ", ".join(f"{n} x {vt}" for vt, n in sorted(counts.items()))

    def _section_title(self, text, subtitle=None):
        tk.Label(self.scrollable_frame, text=text, font=(t.FONT, 13, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 2))
        if subtitle:
            tk.Label(self.scrollable_frame, text=subtitle, font=(t.FONT, 9), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 5))

    # ------------------------------------------------------------------
    # page
    # ------------------------------------------------------------------
    def build_dispatch_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        style_tables()

        page_header(self.scrollable_frame, "Event Dispatch Panel", self.build_dispatch_content)

        events = get_all_events()
        if not events:
            tk.Label(self.scrollable_frame, text="No events scheduled in system.", font=(t.FONT, 10, "italic"), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30)
            return

        # ---- Step 1: event ------------------------------------------------
        sel_card = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
        sel_card.pack(fill=tk.X, padx=30, pady=10, ipady=10, ipadx=15)

        tk.Label(sel_card, text="1. SELECT EVENT", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.PRIMARY).pack(anchor="w", padx=10, pady=(5, 5))

        event_dict = {f"{e['title']} | {e['event_datetime']} | {e['is_recurring']}": e for e in events}
        event_options = list(event_dict.keys())

        selected_event_str = tk.StringVar(sel_card)
        # Keep the event the dispatcher chose across redraws
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
        for label, value in [("Upcoming bookings", bookings_count), ("Guests booked", guests_count),
                             ("Capacity per date", f"{event_capacity['total']} ({capacity_note})")]:
            box = tk.Frame(stats, bg=t.FIELD_BG, padx=12, pady=6)
            box.pack(side=tk.LEFT, padx=(0, 10))
            tk.Label(box, text=label, font=(t.FONT, 8, "bold"), bg=t.FIELD_BG, fg=t.TEXT_MUTED).pack(anchor="w")
            tk.Label(box, text=str(value), font=(t.FONT, 11, "bold"), bg=t.FIELD_BG, fg=t.TEXT).pack(anchor="w")

        seats_by_type = {vt["name"]: vt["capacity"] for vt in get_vehicle_types()}
        vehicles = get_all_vehicles(self.email)
        available_vehicles = [v for v in vehicles if v['status'] == 'Available']
        assigned_vehicles = self.get_assigned_vehicles_for_event(current_event_id)
        for v in assigned_vehicles:
            v.setdefault('capacity', seats_by_type.get(v['vehicle_type'], 4))

        self._build_available_section(current_event, available_vehicles)
        self._build_assigned_section(assigned_vehicles)

    # ------------------------------------------------------------------
    # Step 2 + 3: find and assign available vehicles
    # ------------------------------------------------------------------
    def _build_available_section(self, current_event, available_vehicles):
        self._section_title("2. Find Available Vehicles",
                            "Choose what you need, then press Show. Only vehicles that are free right now are listed.")

        filter_card = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
        filter_card.pack(fill=tk.X, padx=30, pady=5, ipady=8, ipadx=10)

        if not available_vehicles:
            tk.Label(filter_card, text="No available vehicles in your fleet. Free or register vehicles first.",
                     font=(t.FONT, 10, "italic"), bg=t.CARD_BG, fg="#e74c3c").pack(anchor="w", padx=10, pady=5)
            return

        type_options = [ANY_TYPE] + sorted({v['vehicle_type'] for v in available_vehicles})
        location_options = [ANY_LOCATION] + sorted({v['location'] for v in available_vehicles})
        search = self.search or {}
        type_var = tk.StringVar(filter_card, value=search.get("type") if search.get("type") in type_options else ANY_TYPE)
        location_var = tk.StringVar(filter_card, value=search.get("location") if search.get("location") in location_options else ANY_LOCATION)

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
            tk.Label(filter_card, text=f"{len(available_vehicles)} vehicles are free: {self._type_breakdown(available_vehicles)}.",
                     font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=10, pady=(4, 0))
            return

        matches = [v for v in available_vehicles
                   if (self.search["type"] == ANY_TYPE or v['vehicle_type'] == self.search["type"])
                   and (self.search["location"] == ANY_LOCATION or v['location'] == self.search["location"])]
        # Drop selections that are no longer in the result
        self.selected["available"] &= {v['id'] for v in matches}

        if not matches:
            tk.Label(self.scrollable_frame, text="No free vehicles match these filters. Try another type or location.",
                     font=(t.FONT, 10, "italic"), bg=t.PAGE_BG, fg="#e74c3c").pack(anchor="w", padx=30, pady=8)
            return

        visible = [v for v in matches if self._passes_filters("available", v)]
        tk.Label(self.scrollable_frame, text=f"{len(matches)} vehicles found",
                 font=(t.FONT, 10, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(10, 4))
        build_count_table(self.scrollable_frame, [v['vehicle_type'] for v in matches]).pack(anchor="w", padx=30, pady=(0, 10))
        tk.Label(self.scrollable_frame, text=f"Click a row to select it. Click a heading with {GEAR} to filter that column, or {CHECKED} to select all.",
                 font=(t.FONT, 9), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 4))

        summary_var = tk.StringVar()
        tree = self._build_table("available", AVAILABLE_COLUMNS, matches, visible, on_select_change=lambda: refresh_summary())

        # Quick select: several vehicles of the same type in one go
        quick = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        quick.pack(fill=tk.X, padx=30, pady=(6, 0))
        visible_types = sorted({v['vehicle_type'] for v in visible})
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
                same_type = [v['id'] for v in visible if v['vehicle_type'] == qty_type_var.get()]
                wanted = qty_var.get()
                if wanted > len(same_type):
                    messagebox.showwarning("Not enough vehicles", f"Only {len(same_type)} x {qty_type_var.get()} are free with these filters.")
                    wanted = len(same_type)
                # Replace the selection for this type, keep other types as they are
                self.selected["available"] -= set(same_type)
                self.selected["available"] |= set(same_type[:wanted])
                tree.refresh_rows()
                refresh_summary()

            tk.Button(quick, text="Select", font=(t.FONT, 9, "bold"), bg=t.CHIP_BG, fg=t.TEXT, relief="flat",
                      cursor="hand2", command=quick_select).pack(side=tk.LEFT, ipadx=8)
            tk.Button(quick, text="Clear selection", font=(t.FONT, 9), bg=t.PAGE_BG, fg=t.TEXT_MUTED, relief="flat",
                      cursor="hand2", command=lambda: (self.selected["available"].clear(), tree.refresh_rows(), refresh_summary())).pack(side=tk.LEFT, padx=6)

        # ---- Step 3: reassign choice and assign button ----
        self._section_title("3. Assign to Event")
        assign_card = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
        assign_card.pack(fill=tk.X, padx=30, pady=5, ipady=8, ipadx=10)

        tk.Label(assign_card, textvariable=summary_var, font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.TEXT,
                 justify="left", wraplength=700).pack(anchor="w", padx=10, pady=(5, 8))

        tk.Label(assign_card, text="After this event, should these vehicles move on to the next recurring event? (required)",
                 font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=10)
        reassign_var = tk.IntVar(assign_card, value=-1 if self.reassign_choice is None else self.reassign_choice)

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
            available_ids = {v['id'] for v in matches}
            assignments = [{"vehicle_id": vid, "auto_reassign_recurring": self.reassign_choice}
                           for vid in self.selected["available"] if vid in available_ids]
            assigned_count = dispatch_vehicle_combination(current_event['id'], assignments)
            if assigned_count < len(assignments):
                messagebox.showwarning("Partly assigned", f"Assigned {assigned_count} of {len(assignments)} vehicles. The others were taken in the meantime.")
            else:
                messagebox.showinfo("Success", f"Assigned {assigned_count} vehicles to the event.")
            self.selected["available"].clear()
            self.reassign_choice = None
            self.build_dispatch_content()

        assign_btn = tk.Button(assign_card, text=f"{ic.emoji('plus')} Assign Selected Vehicles", font=(t.FONT, 10, "bold"),
                               fg="white", relief="flat", command=handle_assign_vehicles)
        assign_btn.pack(anchor="w", padx=10, pady=(10, 2), ipadx=12, ipady=6)
        hint_label.pack(anchor="w", padx=10, pady=(0, 4))

        def refresh_summary():
            chosen = [v for v in matches if v['id'] in self.selected["available"]]
            if chosen:
                seats = sum(int(v.get('capacity') or 0) for v in chosen)
                summary_var.set(f"Selected: {len(chosen)} vehicles ({self._type_breakdown(chosen)}), {seats} seats")
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

    # ------------------------------------------------------------------
    # Step 4: vehicles already on this event
    # ------------------------------------------------------------------
    def _build_assigned_section(self, assigned_vehicles):
        self._section_title("Assigned Vehicles for This Event")

        if not assigned_vehicles:
            tk.Label(self.scrollable_frame, text="No vehicles currently assigned to this event.", font=(t.FONT, 10, "italic"), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=5)
            return

        self.selected["assigned"] &= {v['id'] for v in assigned_vehicles}
        seats = sum(int(v.get('capacity') or 0) for v in assigned_vehicles)
        tk.Label(self.scrollable_frame, text=f"{len(assigned_vehicles)} vehicles, {seats} seats",
                 font=(t.FONT, 10, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(0, 4))
        build_count_table(self.scrollable_frame, [v['vehicle_type'] for v in assigned_vehicles]).pack(anchor="w", padx=30, pady=(0, 10))

        visible = [v for v in assigned_vehicles if self._passes_filters("assigned", v)]
        btn_frame = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)

        def refresh_button():
            n = len(self.selected["assigned"])
            unassign_btn.config(text=f"{ic.emoji('cross')} Unassign Selected Vehicles ({n})",
                                state=tk.NORMAL if n else tk.DISABLED, bg="#e74c3c" if n else "#bdc3c7")

        self._build_table("assigned", ASSIGNED_COLUMNS, assigned_vehicles, visible, on_select_change=lambda: refresh_button())
        btn_frame.pack(fill=tk.X, padx=30, pady=(6, 20))

        def handle_unassign_vehicles():
            ids = list(self.selected["assigned"])
            if not ids:
                return
            if not messagebox.askyesno("Unassign vehicles", f"Send {len(ids)} vehicles back to the available fleet?"):
                return
            for vid in ids:
                free_vehicle(vid)
            self.selected["assigned"].clear()
            self.build_dispatch_content()

        unassign_btn = tk.Button(btn_frame, font=(t.FONT, 10, "bold"), fg="white", relief="flat", cursor="hand2", command=handle_unassign_vehicles)
        unassign_btn.pack(side=tk.LEFT, ipadx=12, ipady=6)
        refresh_button()

    # ------------------------------------------------------------------
    # shared table
    # ------------------------------------------------------------------
    def _build_table(self, table, columns, all_rows, visible_rows, on_select_change):
        frame = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
        frame.pack(fill=tk.X, padx=30, pady=2)

        col_keys = [c[0] for c in columns]
        tree = ttk.Treeview(frame, columns=col_keys, show="headings", height=min(max(len(visible_rows), 3), 8),
                            style=TABLE_STYLE, selectmode="none")
        stripe_tags(tree)

        selected = self.selected[table]
        visible_ids = [v['id'] for v in visible_rows]

        def toggle_all():
            if visible_ids and all(vid in selected for vid in visible_ids):
                selected.difference_update(visible_ids)
            else:
                selected.update(visible_ids)
            refresh_rows()
            on_select_change()

        for col_key, heading, width, anchor, filterable in columns:
            if col_key == "select":
                tree.heading(col_key, text=heading, command=toggle_all)
            elif filterable:
                tree.heading(col_key, text=heading_text(heading, self._filter_active(table, col_key)), anchor=anchor,
                             command=lambda ck=col_key, h=heading: self._open_filter_window(table, ck, h, all_rows))
            else:
                tree.heading(col_key, text=heading)
            tree.column(col_key, width=width, minwidth=width, anchor=anchor, stretch=col_key not in ("select", "seats"))

        def refresh_rows():
            for i, item in enumerate(tree.get_children()):
                vid = int(item)
                vals = list(tree.item(item, "values"))
                vals[0] = CHECKED if vid in selected else UNCHECKED
                tag = "picked" if vid in selected else ("odd" if i % 2 else "even")
                tree.item(item, values=vals, tags=(tag,))

        for v in visible_rows:
            values = [UNCHECKED] + [self._get_val_for_col(v, ck) for ck in col_keys[1:]]
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
            tk.Label(self.scrollable_frame, text=f"All rows are hidden by your column filters. Click a {GEAR} heading to change them.",
                     font=(t.FONT, 9, "italic"), bg=t.PAGE_BG, fg="#e74c3c").pack(anchor="w", padx=30)

        tree.refresh_rows = refresh_rows
        return tree

    def _open_filter_window(self, table, col_key, col_name, rows):
        popup = tk.Toplevel(self.root)
        popup.title(f"Filter: {col_name}")
        popup.configure(bg=t.CARD_BG)
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()

        tk.Label(popup, text=f"{GEAR} Filter {col_name}", font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=15, pady=(15, 10))

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
            unique_vals = sorted({str(self._get_val_for_col(v, col_key)) for v in rows},
                                 key=lambda s: (0, int(s)) if s.isdigit() else (1, s.lower()))
            hidden = self.hidden[table].get(col_key, set())
            counts = Counter(str(self._get_val_for_col(v, col_key)) for v in rows)
            var_dict = {}

            toggles = tk.Frame(popup, bg=t.CARD_BG)
            toggles.pack(fill=tk.X, padx=15)
            frame_chk = tk.Frame(popup, bg=t.CARD_BG)
            frame_chk.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
            for val in unique_vals:
                var = tk.BooleanVar(value=(val not in hidden))
                var_dict[val] = var
                tk.Checkbutton(frame_chk, text=f"{val}  ({counts[val]})", variable=var, bg=t.CARD_BG, font=(t.FONT, 9),
                               fg=t.TEXT, activebackground=t.CARD_BG, anchor="w").pack(fill=tk.X, pady=1)
            for text, state in [("Select all", True), ("Select none", False)]:
                tk.Button(toggles, text=text, font=(t.FONT, 8), bg=t.CHIP_BG, fg=t.TEXT, relief="flat",
                          command=lambda s=state: [var.set(s) for var in var_dict.values()]).pack(side=tk.LEFT, padx=(0, 6))

            def apply_filter(event=None):
                self.hidden[table][col_key] = {val for val, var in var_dict.items() if not var.get()}
                popup.destroy()
                self.build_dispatch_content()

            def clear_filter():
                self.hidden[table].pop(col_key, None)
                popup.destroy()
                self.build_dispatch_content()

        btns = tk.Frame(popup, bg=t.CARD_BG)
        btns.pack(fill=tk.X, padx=15, pady=15)
        tk.Button(btns, text="Apply Filter", font=(t.FONT, 9, "bold"), bg=t.PRIMARY, fg="white", relief="flat",
                  cursor="hand2", command=apply_filter).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        tk.Button(btns, text="Clear", font=(t.FONT, 9), bg=t.CHIP_BG, fg=t.TEXT, relief="flat",
                  cursor="hand2", command=clear_filter).pack(side=tk.LEFT, padx=(8, 0), ipady=5, ipadx=10)
        popup.bind("<Escape>", lambda e: popup.destroy())
