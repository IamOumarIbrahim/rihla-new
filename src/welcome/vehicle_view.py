import tkinter as tk
from tkinter import messagebox, ttk
import theme as t
import icons as ic
from digit_boxes import DigitBoxes
from .table_style import CHECKED, UNCHECKED, GEAR, TABLE_STYLE, style_tables, heading_text, stripe_tags
from database import get_all_vehicles, create_vehicle, delete_vehicle, update_vehicle_status, free_vehicle, get_vehicle_types


class VehicleView:
    def __init__(self, parent_screen):
        self.parent = parent_screen
        self.root = parent_screen.root
        self.email = parent_screen.email
        self.scrollable_frame = parent_screen.scrollable_frame

        self.column_filters = {}
        self.known_values = {}
        self.id_filter_op = "="
        self.id_filter_val = ""
        self.license_filter_val = ""
        self.selected_ids = set()
        self.select_all_state = False

    def build_register_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        tk.Label(self.scrollable_frame, text=f"Register Vehicles", font=(t.FONT, 22, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 5))
        tk.Label(self.scrollable_frame, text="Add vehicles to the system inventory using their 5-digit license numbers.", font=(t.FONT, 11), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 15))

        form_card = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
        form_card.pack(fill=tk.X, padx=30, pady=10, ipady=20, ipadx=20)

        tk.Label(form_card, text="VEHICLE REGISTRATION FORM", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.PRIMARY).pack(anchor="w", padx=10, pady=(5, 15))

        input_row1 = tk.Frame(form_card, bg=t.CARD_BG)
        input_row1.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(input_row1, text="5-Digit License:", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(side=tk.LEFT)
        # 1 group of 5 boxes: digits only, the cursor moves on after every digit
        license_boxes = DigitBoxes(input_row1, groups=1, group_size=5, font_size=12, bg=t.CARD_BG)
        license_boxes.pack(side=tk.LEFT, padx=(8, 20))
        license_boxes.focus_first()

        tk.Label(input_row1, text="Type:", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(side=tk.LEFT)
        v_types = get_vehicle_types()
        type_names = [vt["name"] for vt in v_types] if v_types else ["desert buggy", "4x4 toyota landcrusier", "mini-yacht", "tesla sedan", "RTA bus"]
        
        type_var = tk.StringVar(form_card)
        type_var.set(type_names[0])
        type_menu = tk.OptionMenu(input_row1, type_var, *type_names)
        type_menu.config(font=(t.FONT, 10), bg=t.FIELD_BG)
        type_menu.pack(side=tk.LEFT, padx=(8, 20))

        tk.Label(input_row1, text="Location:", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(side=tk.LEFT)
        loc_entry = tk.Entry(input_row1, font=(t.FONT, 11), bg=t.FIELD_BG, relief="solid", bd=1, width=22)
        loc_entry.pack(side=tk.LEFT, padx=(8, 0))

        def handle_add_vehicle():
            lic = license_boxes.get()
            v_type = type_var.get()
            location = loc_entry.get().strip()

            if not license_boxes.is_complete():
                license_boxes.set_error(True)
                messagebox.showerror("Error", "License number must be exactly 5 digits.")
                return
            if not location:
                messagebox.showerror("Error", "Location is required.")
                return

            try:
                create_vehicle(lic, v_type, location, self.email, 0)
                messagebox.showinfo("Success", "Vehicle registered successfully!")
                license_boxes.clear()
                loc_entry.delete(0, tk.END)
            except ValueError as e:
                if "UNIQUE" in str(e).upper():
                    messagebox.showerror("Error", f"A vehicle with license number {lic} is already registered.")
                else:
                    messagebox.showerror("Error", f"Could not add vehicle: {e}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not add vehicle: {e}")

        add_btn = tk.Button(form_card, text=f"{ic.emoji('plus')} Register Vehicle", font=(t.FONT, 11, "bold"), bg=t.PRIMARY, fg="white", relief="flat", command=handle_add_vehicle)
        add_btn.pack(anchor="w", padx=10, pady=(20, 5), ipadx=15, ipady=8)
        t.add_hover(add_btn, t.PRIMARY, t.PRIMARY_HOVER)

    def build_fleet_management_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        tk.Label(self.scrollable_frame, text=f"Fleet Maintenance & Status Management", font=(t.FONT, 22, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 5))

        vehicles = get_all_vehicles(self.email)

        # Values seen for the first time (new vehicle, new status...) are shown by default.
        # Before this fix, a vehicle set to "Maintenance" disappeared from the table.
        for col_key in ["type", "location", "status", "capacity", "reassign"]:
            current_vals = set(str(self._get_val_for_col(v, col_key)) for v in vehicles)
            known_vals = self.known_values.setdefault(col_key, set())
            self.column_filters.setdefault(col_key, set()).update(current_vals - known_vals)
            known_vals.update(current_vals)

        style_tables()


        table_frame = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
        table_frame.pack(fill=tk.X, padx=30, pady=5)

        # (key, heading, width, anchor)
        columns_meta = [
            ("select", CHECKED, 50, "center"),
            ("id", "ID", 70, "center"),
            ("license", "License Number", 140, "center"),
            ("type", "Vehicle Type", 190, "w"),
            ("capacity", "Capacity", 100, "center"),
            ("location", "Location", 180, "w"),
            ("status", "Status", 110, "center"),
            ("reassign", "Auto-Reassign", 130, "center"),
        ]

        col_keys = [c[0] for c in columns_meta]
        tree = ttk.Treeview(table_frame, columns=col_keys, show="headings", height=10, style=TABLE_STYLE, selectmode="none")
        stripe_tags(tree)

        for col_key, col_name, width, anchor in columns_meta:
            if col_key == "select":
                tree.heading(col_key, text=col_name, command=self.toggle_select_all_rows)
            else:
                tree.heading(col_key, text=heading_text(col_name, self._filter_active(col_key)), anchor=anchor,
                             command=lambda ck=col_key, cn=col_name: self.open_filter_window(ck, cn, vehicles))
            tree.column(col_key, width=width, minwidth=width, anchor=anchor, stretch=col_key not in ("select", "id"))

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def load_filtered_tree():
            for row in tree.get_children():
                tree.delete(row)

            for i, v in enumerate(v for v in vehicles if self._is_visible(v)):
                vid = v['id']
                picked = vid in self.selected_ids
                reassign_text = "Yes" if v['auto_reassign_recurring'] else "No"
                tree.insert("", tk.END, iid=str(vid), tags=("picked" if picked else ("odd" if i % 2 else "even"),),
                            values=(CHECKED if picked else UNCHECKED, vid, v['license_number'], v['vehicle_type'],
                                    v['capacity'], v['location'], v['status'], reassign_text))

        load_filtered_tree()

        def on_table_click(event):
            if tree.identify("region", event.x, event.y) != "cell":
                return
            item = tree.identify_row(event.y)
            if not item:
                return
            vid = int(item)
            if vid in self.selected_ids:
                self.selected_ids.remove(vid)
            else:
                self.selected_ids.add(vid)
            load_filtered_tree()

        tree.bind("<Button-1>", on_table_click)

        btn_frame = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        btn_frame.pack(fill=tk.X, padx=30, pady=15)

        del_btn = tk.Button(btn_frame, text=f"Delete Selected", bg="#e74c3c", fg="white", font=(t.FONT, 9, "bold"), relief="flat", command=lambda: self.handle_delete(vehicles))
        del_btn.pack(side=tk.LEFT, padx=(0, 10), ipadx=10, ipady=6)

        maint_btn = tk.Button(btn_frame, text=f"Set Maintenance", bg="#f39c12", fg="white", font=(t.FONT, 9, "bold"), relief="flat", command=lambda: self.handle_status("Maintenance"))
        maint_btn.pack(side=tk.LEFT, padx=(0, 10), ipadx=10, ipady=6)

        # One button: making a vehicle available also releases it from any event it was assigned to.
        avail_btn = tk.Button(btn_frame, text=f"Set Available", bg="#27ae60", fg="white", font=(t.FONT, 9, "bold"), relief="flat", command=self.handle_available)
        avail_btn.pack(side=tk.LEFT, ipadx=10, ipady=6)

    def handle_delete(self, vehicles):
        if not self.selected_ids:
            messagebox.showerror("Error", "Please select at least one vehicle.")
            return
        if messagebox.askyesno("Confirm", f"Delete {len(self.selected_ids)} selected vehicles?"):
            for vid in self.selected_ids:
                delete_vehicle(vid)
            self.selected_ids.clear()
            self.build_fleet_management_content()

    def handle_status(self, new_status):
        if not self.selected_ids:
            messagebox.showerror("Error", "Please select at least one vehicle.")
            return
        for vid in self.selected_ids:
            update_vehicle_status(vid, new_status)
        messagebox.showinfo("Success", f"Updated status to {new_status}.")
        self.build_fleet_management_content()

    def handle_available(self):
        if not self.selected_ids:
            messagebox.showerror("Error", "Please select at least one vehicle.")
            return
        for vid in self.selected_ids:
            free_vehicle(vid)
        messagebox.showinfo("Success", "Vehicles set to Available and released from their events.")
        self.build_fleet_management_content()

    def toggle_select_all_rows(self):
        vehicles = get_all_vehicles(self.email)
        all_ids = {v['id'] for v in vehicles if self._is_visible(v)}
        if self.select_all_state:
            self.selected_ids.clear()
            self.select_all_state = False
        else:
            self.selected_ids = all_ids
            self.select_all_state = True
        self.build_fleet_management_content()

    def _filter_active(self, col_key):
        if col_key == "id":
            return bool(self.id_filter_val)
        if col_key == "license":
            return bool(self.license_filter_val)
        return self.column_filters.get(col_key, set()) != self.known_values.get(col_key, set())

    def _is_visible(self, v):
        """Same rules as the table, so 'select all' only picks rows the user can see."""
        if self.id_filter_val:
            try:
                target = int(self.id_filter_val)
                if self.id_filter_op == "=" and v['id'] != target:
                    return False
                if self.id_filter_op == ">" and v['id'] <= target:
                    return False
                if self.id_filter_op == "<" and v['id'] >= target:
                    return False
            except ValueError:
                pass
        if self.license_filter_val and str(v['license_number']).strip() != str(self.license_filter_val).strip():
            return False
        for ck in ["type", "location", "status", "capacity", "reassign"]:
            if str(self._get_val_for_col(v, ck)) not in self.column_filters.get(ck, set()):
                return False
        return True

    def _get_val_for_col(self, v, col_key):
        if col_key == "id":
            return v['id']
        elif col_key == "license":
            return v['license_number']
        elif col_key == "type":
            return v['vehicle_type']
        elif col_key == "capacity":
            return str(v['capacity'])
        elif col_key == "location":
            return v['location']
        elif col_key == "status":
            return v['status']
        elif col_key == "reassign":
            return "Yes" if v['auto_reassign_recurring'] else "No"
        return ""

    def open_filter_window(self, col_key, col_name, vehicles):
        popup = tk.Toplevel(self.root)
        popup.title(f"Filter: {col_name}")
        popup.geometry("280x300")
        popup.configure(bg=t.CARD_BG)
        popup.resizable(False, False)

        tk.Label(popup, text=f"{GEAR} Filter {col_name}", font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=15, pady=(15, 10))

        if col_key == "id":
            tk.Label(popup, text="Condition:", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=(5, 2))
            op_var = tk.StringVar(popup, value=self.id_filter_op)
            tk.OptionMenu(popup, op_var, "=", ">", "<").pack(fill=tk.X, padx=15, pady=5)
            tk.Label(popup, text="Value:", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=(5, 2))
            val_entry = tk.Entry(popup, font=(t.FONT, 10), bg=t.FIELD_BG)
            val_entry.pack(fill=tk.X, padx=15, pady=5)
            if self.id_filter_val: val_entry.insert(0, str(self.id_filter_val))

            def apply_filter():
                self.id_filter_op = op_var.get()
                self.id_filter_val = val_entry.get().strip()
                popup.destroy()
                self.build_fleet_management_content()
            tk.Button(popup, text="Apply Filter", bg=t.PRIMARY, fg="white", command=apply_filter).pack(fill=tk.X, padx=15, pady=20, ipady=5)

        elif col_key == "license":
            tk.Label(popup, text="License:", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=(5, 2))
            lic_boxes = DigitBoxes(popup, groups=1, group_size=5, font_size=12, initial=self.license_filter_val)
            lic_boxes.pack(anchor="w", padx=15, pady=5)
            lic_boxes.focus_first()
            tk.Label(popup, text="Leave empty to show all licenses.", font=(t.FONT, 8), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15)

            def apply_filter():
                if lic_boxes.get() and not lic_boxes.is_complete():
                    lic_boxes.set_error(True)
                    return
                self.license_filter_val = lic_boxes.get()
                popup.destroy()
                self.build_fleet_management_content()
            tk.Button(popup, text="Apply Filter", bg=t.PRIMARY, fg="white", command=apply_filter).pack(fill=tk.X, padx=15, pady=20, ipady=5)

        else:
            unique_vals = sorted(list(set(str(self._get_val_for_col(v, col_key)) for v in vehicles)))
            current_allowed = self.column_filters.get(col_key, set(unique_vals))
            frame_chk = tk.Frame(popup, bg=t.CARD_BG)
            frame_chk.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
            var_dict = {}
            for val in unique_vals:
                var = tk.BooleanVar(value=(val in current_allowed))
                var_dict[val] = var
                tk.Checkbutton(frame_chk, text=val, variable=var, bg=t.CARD_BG, font=(t.FONT, 9)).pack(anchor="w", pady=2)

            def apply_filter():
                self.column_filters[col_key] = {val for val, var in var_dict.items() if var.get()}
                popup.destroy()
                self.build_fleet_management_content()
            tk.Button(popup, text="Apply Filter", bg=t.PRIMARY, fg="white", command=apply_filter).pack(fill=tk.X, padx=15, pady=15, ipady=5)