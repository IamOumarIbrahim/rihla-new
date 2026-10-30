import tkinter as tk
from tkinter import messagebox, ttk
import theme as t
from database import get_all_vehicles, get_all_events, dispatch_vehicle_combination, free_vehicle, _connect, get_event_demand, get_event_capacity


class DispatchView:
    def __init__(self, parent_screen):
        self.parent = parent_screen
        self.root = parent_screen.root
        self.email = parent_screen.email
        self.scrollable_frame = parent_screen.scrollable_frame

        # Available table filters & selections
        self.current_event_key = None
        self.known_dispatch_values = {}
        self.known_assigned_values = {}
        self.dispatch_selected_ids = set()
        self.dispatch_select_all_state = False
        self.dispatch_column_filters = {}
        self.dispatch_id_filter_op = "="
        self.dispatch_id_filter_val = ""
        self.dispatch_license_filter_val = ""

        # Assigned table filters & selections
        self.assigned_selected_ids = set()
        self.assigned_select_all_state = False
        self.assigned_column_filters = {}
        self.assigned_id_filter_op = "="
        self.assigned_id_filter_val = ""
        self.assigned_license_filter_val = ""

    def _get_val_for_col(self, v, col_key):
        if col_key == "id":
            return v['id']
        elif col_key == "license":
            return v['license_number']
        elif col_key == "type":
            return v['vehicle_type']
        elif col_key == "location":
            return v['location']
        elif col_key == "status":
            return v['status']
        elif col_key == "reassign":
            return "Yes" if v.get('auto_reassign_recurring', 0) else "No"
        return ""

    def get_assigned_vehicles_for_event(self, event_id):
        with _connect() as conn:
            rows = conn.execute('''
                SELECT v.id, v.license_number, v.vehicle_type, v.location, v.status, v.auto_reassign_recurring
                FROM event_vehicles ev
                JOIN vehicles v ON ev.vehicle_id = v.id
                WHERE ev.event_id = ? AND ev.status = 'Assigned'
            ''', (event_id,)).fetchall()
        return [{"id": r[0], "license_number": r[1], "vehicle_type": r[2], "location": r[3], "status": r[4], "auto_reassign_recurring": r[5]} for r in rows]

    def build_dispatch_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        tk.Label(self.scrollable_frame, text="Event Dispatch Panel", font=(t.FONT, 22, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 5))
        tk.Label(self.scrollable_frame, text="Select an event to manage available and assigned vehicle combinations.", font=(t.FONT, 11), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 15))

        events = get_all_events()
        if not events:
            tk.Label(self.scrollable_frame, text="No events scheduled in system.", font=(t.FONT, 10, "italic"), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30)
            return

        # Target Event Selector Card
        sel_card = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
        sel_card.pack(fill=tk.X, padx=30, pady=10, ipady=15, ipadx=15)

        tk.Label(sel_card, text="SELECT TARGET EVENT", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.PRIMARY).pack(anchor="w", padx=10, pady=(5, 5))

        event_dict = {f"{e['title']} | {e['event_datetime']} | {e['is_recurring']}": e['id'] for e in events}
        event_options = list(event_dict.keys())

        selected_event_str = tk.StringVar(sel_card)
        # Keep the event the dispatcher chose. Before this fix every redraw jumped back to the first event.
        if self.current_event_key in event_dict:
            selected_event_str.set(self.current_event_key)
        else:
            selected_event_str.set(event_options[0] if event_options else "")

        # Re-build content on event change
        def on_event_change(*args):
            self.current_event_key = selected_event_str.get()
            self.dispatch_selected_ids.clear()
            self.assigned_selected_ids.clear()
            self.build_dispatch_content()

        selected_event_str.trace_add("write", on_event_change)

        event_menu = tk.OptionMenu(sel_card, selected_event_str, *event_options)
        event_menu.config(font=(t.FONT, 10), bg=t.FIELD_BG)
        event_menu.pack(fill=tk.X, padx=10, pady=5)

        current_event_id = event_dict[selected_event_str.get()]
        bookings_count, guests_count = get_event_demand(current_event_id)
        tk.Label(sel_card, text=f"Upcoming bookings: {bookings_count}   |   Guests booked: {guests_count}", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=10, pady=(0, 5))
        event_capacity = get_event_capacity(current_event_id)
        if event_capacity["source"] == "vehicles":
            capacity_text = f"Capacity: {event_capacity['total']} guests per date (total seats of the assigned vehicles)"
        else:
            capacity_text = f"Capacity: {event_capacity['total']} guests per date (set by the vendor, no vehicles assigned)"
        tk.Label(sel_card, text=capacity_text, font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=10, pady=(0, 5))

        vehicles = get_all_vehicles(self.email)
        available_vehicles = [v for v in vehicles if v['status'] == 'Available']
        assigned_vehicles = self.get_assigned_vehicles_for_event(current_event_id)

        # ---------------------------------------------------------
        # TABLE 1: AVAILABLE VEHICLES
        # ---------------------------------------------------------
        tk.Label(self.scrollable_frame, text="Available Vehicles", font=(t.FONT, 13, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(15, 5))

        if not available_vehicles:
            tk.Label(self.scrollable_frame, text="No available vehicles found in fleet.", font=(t.FONT, 10, "italic"), bg=t.PAGE_BG, fg="#e74c3c").pack(anchor="w", padx=30, pady=5)
        else:
            for col_key in ["type", "location", "status", "reassign"]:
                current_vals = set(str(self._get_val_for_col(v, col_key)) for v in available_vehicles)
                known_vals = self.known_dispatch_values.setdefault(col_key, set())
                self.dispatch_column_filters.setdefault(col_key, set()).update(current_vals - known_vals)
                known_vals.update(current_vals)

            table_frame1 = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
            table_frame1.pack(fill=tk.X, padx=30, pady=5)

            columns_meta = [
                ("select", "[x]"),
                ("id", "ID "),
                ("license", "License Number "),
                ("type", "Vehicle Type "),
                ("location", "Location "),
                ("status", "Status "),
                ("reassign", "Auto-Reassign ")
            ]

            col_keys = [c[0] for c in columns_meta]
            tree1 = ttk.Treeview(table_frame1, columns=col_keys, show="headings", height=6)

            for col_key, col_name in columns_meta:
                if col_key == "select":
                    tree1.heading(col_key, text=col_name, command=lambda: self.toggle_dispatch_select_all(available_vehicles, tree1))
                else:
                    tree1.heading(col_key, text=col_name, command=lambda ck=col_key, cn=col_name: self.open_dispatch_filter_window(ck, cn, available_vehicles))

            tree1.column("select", width=50, anchor="center")
            tree1.column("id", width=60, anchor="center")
            tree1.column("license", width=120, anchor="center")
            tree1.column("type", width=140, anchor="w")
            tree1.column("location", width=150, anchor="w")
            tree1.column("status", width=100, anchor="center")
            tree1.column("reassign", width=100, anchor="center")

            scrollbar1 = ttk.Scrollbar(table_frame1, orient=tk.VERTICAL, command=tree1.yview)
            tree1.configure(yscrollcommand=scrollbar1.set)
            tree1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar1.pack(side=tk.RIGHT, fill=tk.Y)

            for v in available_vehicles:
                vid = v['id']
                if self.dispatch_id_filter_val:
                    try:
                        target = int(self.dispatch_id_filter_val)
                        val = int(vid)
                        if self.dispatch_id_filter_op == "=" and val != target: continue
                        if self.dispatch_id_filter_op == ">" and val <= target: continue
                        if self.dispatch_id_filter_op == "<" and val >= target: continue
                    except ValueError:
                        pass
                if self.dispatch_license_filter_val and str(v['license_number']).strip() != str(self.dispatch_license_filter_val).strip():
                    continue

                match = True
                for ck in ["type", "location", "status", "reassign"]:
                    val = str(self._get_val_for_col(v, ck))
                    if val not in self.dispatch_column_filters.get(ck, set()):
                        match = False
                        break
                if match:
                    chk_symbol = "[x]" if vid in self.dispatch_selected_ids else "[ ]"
                    reassign_text = "Yes" if v['auto_reassign_recurring'] else "No"
                    tree1.insert("", tk.END, values=(chk_symbol, vid, v['license_number'], v['vehicle_type'], v['location'], v['status'], reassign_text))

            def on_tree1_click(event):
                region = tree1.identify("region", event.x, event.y)
                if region == "cell":
                    col = tree1.identify_column(event.x)
                    if col == "#1":
                        item = tree1.identify_row(event.y)
                        if item:
                            vals = tree1.item(item, "values")
                            vid = int(vals[1])
                            if vid in self.dispatch_selected_ids:
                                self.dispatch_selected_ids.remove(vid)
                            else:
                                self.dispatch_selected_ids.add(vid)
                            self.build_dispatch_content()

            tree1.bind("<Button-1>", on_tree1_click)

            btn_frame1 = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
            btn_frame1.pack(fill=tk.X, padx=30, pady=5)

            def handle_assign_vehicles():
                if not self.dispatch_selected_ids:
                    messagebox.showerror("Error", "Please select available vehicles to assign.")
                    return
                # Keep each vehicle's own auto-reassign setting (it used to be reset to 0),
                # and only assign vehicles that are really in the Available list.
                reassign_by_id = {v['id']: v['auto_reassign_recurring'] for v in available_vehicles}
                assignments = [{"vehicle_id": vid, "auto_reassign_recurring": reassign_by_id[vid]} for vid in self.dispatch_selected_ids if vid in reassign_by_id]
                if not assignments:
                    messagebox.showerror("Error", "The selected vehicles are no longer available.")
                    self.dispatch_selected_ids.clear()
                    self.build_dispatch_content()
                    return
                assigned_count = dispatch_vehicle_combination(current_event_id, assignments)
                messagebox.showinfo("Success", f"Assigned {assigned_count} vehicles to event!")
                self.dispatch_selected_ids.clear()
                self.build_dispatch_content()

            assign_btn = tk.Button(btn_frame1, text="Assign Selected Vehicles", font=(t.FONT, 10, "bold"), bg=t.ACCENT, fg="white", relief="flat", command=handle_assign_vehicles)
            assign_btn.pack(side=tk.LEFT, ipadx=12, ipady=6)
            t.add_hover(assign_btn, t.ACCENT, "#e67e22")

        # ---------------------------------------------------------
        # TABLE 2: ASSIGNED VEHICLES FOR THIS EVENT
        # ---------------------------------------------------------
        tk.Label(self.scrollable_frame, text="Assigned Vehicles for Event", font=(t.FONT, 13, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 5))

        if not assigned_vehicles:
            tk.Label(self.scrollable_frame, text="No vehicles currently assigned to this event.", font=(t.FONT, 10, "italic"), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=5)
        else:
            for col_key in ["type", "location", "status", "reassign"]:
                current_vals = set(str(self._get_val_for_col(v, col_key)) for v in assigned_vehicles)
                known_vals = self.known_assigned_values.setdefault(col_key, set())
                self.assigned_column_filters.setdefault(col_key, set()).update(current_vals - known_vals)
                known_vals.update(current_vals)

            table_frame2 = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
            table_frame2.pack(fill=tk.X, padx=30, pady=5)

            columns_meta2 = [
                ("select", "[x]"),
                ("id", "ID "),
                ("license", "License Number "),
                ("type", "Vehicle Type "),
                ("location", "Location "),
                ("status", "Status "),
                ("reassign", "Auto-Reassign ")
            ]

            col_keys2 = [c[0] for c in columns_meta2]
            tree2 = ttk.Treeview(table_frame2, columns=col_keys2, show="headings", height=6)

            for col_key, col_name in columns_meta2:
                if col_key == "select":
                    tree2.heading(col_key, text=col_name, command=lambda: self.toggle_assigned_select_all(assigned_vehicles, tree2))
                else:
                    tree2.heading(col_key, text=col_name, command=lambda ck=col_key, cn=col_name: self.open_assigned_filter_window(ck, cn, assigned_vehicles))

            tree2.column("select", width=50, anchor="center")
            tree2.column("id", width=60, anchor="center")
            tree2.column("license", width=120, anchor="center")
            tree2.column("type", width=140, anchor="w")
            tree2.column("location", width=150, anchor="w")
            tree2.column("status", width=100, anchor="center")
            tree2.column("reassign", width=100, anchor="center")

            scrollbar2 = ttk.Scrollbar(table_frame2, orient=tk.VERTICAL, command=tree2.yview)
            tree2.configure(yscrollcommand=scrollbar2.set)
            tree2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)

            for v in assigned_vehicles:
                vid = v['id']
                if self.assigned_id_filter_val:
                    try:
                        target = int(self.assigned_id_filter_val)
                        val = int(vid)
                        if self.assigned_id_filter_op == "=" and val != target: continue
                        if self.assigned_id_filter_op == ">" and val <= target: continue
                        if self.assigned_id_filter_op == "<" and val >= target: continue
                    except ValueError:
                        pass
                if self.assigned_license_filter_val and str(v['license_number']).strip() != str(self.assigned_license_filter_val).strip():
                    continue

                match = True
                for ck in ["type", "location", "status", "reassign"]:
                    val = str(self._get_val_for_col(v, ck))
                    if val not in self.assigned_column_filters.get(ck, set()):
                        match = False
                        break
                if match:
                    chk_symbol = "[x]" if vid in self.assigned_selected_ids else "[ ]"
                    reassign_text = "Yes" if v['auto_reassign_recurring'] else "No"
                    tree2.insert("", tk.END, values=(chk_symbol, vid, v['license_number'], v['vehicle_type'], v['location'], v['status'], reassign_text))

            def on_tree2_click(event):
                region = tree2.identify("region", event.x, event.y)
                if region == "cell":
                    col = tree2.identify_column(event.x)
                    if col == "#1":
                        item = tree2.identify_row(event.y)
                        if item:
                            vals = tree2.item(item, "values")
                            vid = int(vals[1])
                            if vid in self.assigned_selected_ids:
                                self.assigned_selected_ids.remove(vid)
                            else:
                                self.assigned_selected_ids.add(vid)
                            self.build_dispatch_content()

            tree2.bind("<Button-1>", on_tree2_click)

            btn_frame2 = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
            btn_frame2.pack(fill=tk.X, padx=30, pady=5)

            def handle_unassign_vehicles():
                if not self.assigned_selected_ids:
                    messagebox.showerror("Error", "Please select assigned vehicles to unassign.")
                    return
                for vid in self.assigned_selected_ids:
                    free_vehicle(vid)
                messagebox.showinfo("Success", f"Unassigned {len(self.assigned_selected_ids)} vehicles back to available fleet!")
                self.assigned_selected_ids.clear()
                self.build_dispatch_content()

            unassign_btn = tk.Button(btn_frame2, text="Unassign Selected Vehicles", font=(t.FONT, 10, "bold"), bg="#e74c3c", fg="white", relief="flat", command=handle_unassign_vehicles)
            unassign_btn.pack(side=tk.LEFT, ipadx=12, ipady=6)

    def toggle_dispatch_select_all(self, available_vehicles, tree):
        all_ids = {v['id'] for v in available_vehicles}
        if self.dispatch_select_all_state:
            self.dispatch_selected_ids.clear()
            self.dispatch_select_all_state = False
        else:
            self.dispatch_selected_ids = all_ids
            self.dispatch_select_all_state = True
        self.build_dispatch_content()

    def toggle_assigned_select_all(self, assigned_vehicles, tree):
        all_ids = {v['id'] for v in assigned_vehicles}
        if self.assigned_select_all_state:
            self.assigned_selected_ids.clear()
            self.assigned_select_all_state = False
        else:
            self.assigned_selected_ids = all_ids
            self.assigned_select_all_state = True
        self.build_dispatch_content()

    def open_dispatch_filter_window(self, col_key, col_name, available_vehicles):
        popup = tk.Toplevel(self.root)
        popup.title(f"Filter Available: {col_name}")
        popup.geometry("280x300")
        popup.configure(bg=t.CARD_BG)
        popup.resizable(False, False)

        tk.Label(popup, text=f"Filter {col_name}", font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=15, pady=(15, 10))

        if col_key == "id":
            tk.Label(popup, text="Select Condition:", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=(5, 2))
            op_var = tk.StringVar(popup)
            op_var.set(self.dispatch_id_filter_op)
            op_menu = tk.OptionMenu(popup, op_var, "=", ">", "<")
            op_menu.config(font=(t.FONT, 10), bg=t.FIELD_BG)
            op_menu.pack(fill=tk.X, padx=15, pady=5)

            tk.Label(popup, text="Numeric Value:", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=(5, 2))
            val_entry = tk.Entry(popup, font=(t.FONT, 10), bg=t.FIELD_BG, relief="solid", bd=1)
            val_entry.pack(fill=tk.X, padx=15, pady=5)
            if self.dispatch_id_filter_val: val_entry.insert(0, str(self.dispatch_id_filter_val))

            def apply_filter():
                self.dispatch_id_filter_op = op_var.get()
                self.dispatch_id_filter_val = val_entry.get().strip()
                popup.destroy()
                self.build_dispatch_content()
            tk.Button(popup, text="Apply Filter", font=(t.FONT, 9, "bold"), bg=t.PRIMARY, fg="white", relief="flat", command=apply_filter).pack(fill=tk.X, padx=15, pady=20, ipady=5)

        elif col_key == "license":
            tk.Label(popup, text="License Plate Number:", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=(5, 2))
            lic_entry = tk.Entry(popup, font=(t.FONT, 10), bg=t.FIELD_BG, relief="solid", bd=1)
            lic_entry.pack(fill=tk.X, padx=15, pady=5)
            if self.dispatch_license_filter_val: lic_entry.insert(0, str(self.dispatch_license_filter_val))

            def apply_filter():
                self.dispatch_license_filter_val = lic_entry.get().strip()
                popup.destroy()
                self.build_dispatch_content()
            tk.Button(popup, text="Apply Filter", font=(t.FONT, 9, "bold"), bg=t.PRIMARY, fg="white", relief="flat", command=apply_filter).pack(fill=tk.X, padx=15, pady=20, ipady=5)

        else:
            unique_vals = sorted(list(set(str(self._get_val_for_col(v, col_key)) for v in available_vehicles)))
            current_allowed = self.dispatch_column_filters.get(col_key, set(unique_vals))
            frame_chk = tk.Frame(popup, bg=t.CARD_BG)
            frame_chk.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
            var_dict = {}
            for val in unique_vals:
                var = tk.BooleanVar(value=(val in current_allowed))
                var_dict[val] = var
                tk.Checkbutton(frame_chk, text=val, variable=var, bg=t.CARD_BG, font=(t.FONT, 9), fg=t.TEXT).pack(anchor="w", pady=2)

            def apply_filter():
                self.dispatch_column_filters[col_key] = {val for val, var in var_dict.items() if var.get()}
                popup.destroy()
                self.build_dispatch_content()
            tk.Button(popup, text="Apply Filter", font=(t.FONT, 9, "bold"), bg=t.PRIMARY, fg="white", relief="flat", command=apply_filter).pack(fill=tk.X, padx=15, pady=15, ipady=5)

    def open_assigned_filter_window(self, col_key, col_name, assigned_vehicles):
        popup = tk.Toplevel(self.root)
        popup.title(f"Filter Assigned: {col_name}")
        popup.geometry("280x300")
        popup.configure(bg=t.CARD_BG)
        popup.resizable(False, False)

        tk.Label(popup, text=f"Filter {col_name}", font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=15, pady=(15, 10))

        if col_key == "id":
            tk.Label(popup, text="Select Condition:", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=(5, 2))
            op_var = tk.StringVar(popup)
            op_var.set(self.assigned_id_filter_op)
            op_menu = tk.OptionMenu(popup, op_var, "=", ">", "<")
            op_menu.config(font=(t.FONT, 10), bg=t.FIELD_BG)
            op_menu.pack(fill=tk.X, padx=15, pady=5)

            tk.Label(popup, text="Numeric Value:", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=(5, 2))
            val_entry = tk.Entry(popup, font=(t.FONT, 10), bg=t.FIELD_BG, relief="solid", bd=1)
            val_entry.pack(fill=tk.X, padx=15, pady=5)
            if self.assigned_id_filter_val: val_entry.insert(0, str(self.assigned_id_filter_val))

            def apply_filter():
                self.assigned_id_filter_op = op_var.get()
                self.assigned_id_filter_val = val_entry.get().strip()
                popup.destroy()
                self.build_dispatch_content()
            tk.Button(popup, text="Apply Filter", font=(t.FONT, 9, "bold"), bg=t.PRIMARY, fg="white", relief="flat", command=apply_filter).pack(fill=tk.X, padx=15, pady=20, ipady=5)

        elif col_key == "license":
            tk.Label(popup, text="License Plate Number:", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=(5, 2))
            lic_entry = tk.Entry(popup, font=(t.FONT, 10), bg=t.FIELD_BG, relief="solid", bd=1)
            lic_entry.pack(fill=tk.X, padx=15, pady=5)
            if self.assigned_license_filter_val: lic_entry.insert(0, str(self.assigned_license_filter_val))

            def apply_filter():
                self.assigned_license_filter_val = lic_entry.get().strip()
                popup.destroy()
                self.build_dispatch_content()
            tk.Button(popup, text="Apply Filter", font=(t.FONT, 9, "bold"), bg=t.PRIMARY, fg="white", relief="flat", command=apply_filter).pack(fill=tk.X, padx=15, pady=20, ipady=5)

        else:
            unique_vals = sorted(list(set(str(self._get_val_for_col(v, col_key)) for v in assigned_vehicles)))
            current_allowed = self.assigned_column_filters.get(col_key, set(unique_vals))
            frame_chk = tk.Frame(popup, bg=t.CARD_BG)
            frame_chk.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
            var_dict = {}
            for val in unique_vals:
                var = tk.BooleanVar(value=(val in current_allowed))
                var_dict[val] = var
                tk.Checkbutton(frame_chk, text=val, variable=var, bg=t.CARD_BG, font=(t.FONT, 9), fg=t.TEXT).pack(anchor="w", pady=2)

            def apply_filter():
                self.assigned_column_filters[col_key] = {val for val, var in var_dict.items() if var.get()}
                popup.destroy()
                self.build_dispatch_content()
            tk.Button(popup, text="Apply Filter", font=(t.FONT, 9, "bold"), bg=t.PRIMARY, fg="white", relief="flat", command=apply_filter).pack(fill=tk.X, padx=15, pady=15, ipady=5)