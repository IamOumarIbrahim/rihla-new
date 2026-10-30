import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
import theme as t
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

        tk.Label(self.scrollable_frame, text="Register New Vehicles", font=(t.FONT, 22, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 5))
        tk.Label(self.scrollable_frame, text="Add vehicles to the system inventory using their 5-digit license numbers.", font=(t.FONT, 11), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 15))

        form_card = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
        form_card.pack(fill=tk.X, padx=30, pady=10, ipady=20, ipadx=20)

        tk.Label(form_card, text="VEHICLE REGISTRATION FORM", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.PRIMARY).pack(anchor="w", padx=10, pady=(5, 15))

        input_row1 = tk.Frame(form_card, bg=t.CARD_BG)
        input_row1.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(input_row1, text="5-Digit License:", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(side=tk.LEFT)
        license_entry = tk.Entry(input_row1, font=(t.FONT, 11), bg=t.FIELD_BG, relief="solid", bd=1, width=12)
        license_entry.pack(side=tk.LEFT, padx=(8, 20))

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
            lic = license_entry.get().strip()
            v_type = type_var.get()
            location = loc_entry.get().strip()

            if not lic or len(lic) != 5 or not lic.isdigit():
                messagebox.showerror("Error", "License number must be exactly 5 digits.")
                return
            if not location:
                messagebox.showerror("Error", "Location is required.")
                return

            try:
                create_vehicle(lic, v_type, location, self.email, 0)
                messagebox.showinfo("Success", "Vehicle registered successfully!")
                license_entry.delete(0, tk.END)
                loc_entry.delete(0, tk.END)
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", f"A vehicle with license number {lic} is already registered.")
            except Exception as e:
                messagebox.showerror("Error", f"Could not add vehicle: {e}")

        add_btn = tk.Button(form_card, text="Register Vehicle", font=(t.FONT, 11, "bold"), bg=t.PRIMARY, fg="white", relief="flat", command=handle_add_vehicle)
        add_btn.pack(anchor="w", padx=10, pady=(20, 5), ipadx=15, ipady=8)
        t.add_hover(add_btn, t.PRIMARY, t.PRIMARY_HOVER)

    def build_fleet_management_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        tk.Label(self.scrollable_frame, text="Fleet Maintenance & Status Management", font=(t.FONT, 22, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 5))
        tk.Label(self.scrollable_frame, text="Filter, sort, select vehicles, and view their assigned capacities.", font=(t.FONT, 11), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 15))

        vehicles = get_all_vehicles(self.email)

        # Values seen for the first time (new vehicle, new status...) are shown by default.
        # Before this fix, a vehicle set to "Maintenance" disappeared from the table.
        for col_key in ["type", "location", "status", "capacity", "reassign"]:
            current_vals = set(str(self._get_val_for_col(v, col_key)) for v in vehicles)
            known_vals = self.known_values.setdefault(col_key, set())
            self.column_filters.setdefault(col_key, set()).update(current_vals - known_vals)
            known_vals.update(current_vals)

        table_frame = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
        table_frame.pack(fill=tk.X, padx=30, pady=5)

        columns_meta = [
            ("select", "☑"),
            ("id", "ID ⚙️"),
            ("license", "License Number ⚙️"),
            ("type", "Vehicle Type ⚙️"),
            ("capacity", "Capacity ⚙️"),
            ("location", "Location ⚙️"),
            ("status", "Status ⚙️"),
            ("reassign", "Auto-Reassign ⚙️")
        ]

        col_keys = [c[0] for c in columns_meta]
        tree = ttk.Treeview(table_frame, columns=col_keys, show="headings", height=10)

        for col_key, col_name in columns_meta:
            if col_key == "select":
                tree.heading(col_key, text=col_name, command=self.toggle_select_all_rows)
            else:
                tree.heading(col_key, text=col_name, command=lambda ck=col_key, cn=col_name: self.open_filter_window(ck, cn, vehicles))

        tree.column("select", width=50, anchor="center")
        tree.column("id", width=60, anchor="center")
        tree.column("license", width=110, anchor="center")
        tree.column("type", width=130, anchor="w")
        tree.column("capacity", width=80, anchor="center")
        tree.column("location", width=140, anchor="w")
        tree.column("status", width=90, anchor="center")
        tree.column("reassign", width=90, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def load_filtered_tree():
            for row in tree.get_children():
                tree.delete(row)
            
            for v in vehicles:
                vid = v['id']
                lic = v['license_number']
                if self.id_filter_val:
                    try:
                        target = int(self.id_filter_val)
                        val = int(vid)
                        if self.id_filter_op == "=" and val != target: continue
                        if self.id_filter_op == ">" and val <= target: continue
                        if self.id_filter_op == "<" and val >= target: continue
                    except ValueError:
                        pass
                if self.license_filter_val and str(lic).strip() != str(self.license_filter_val).strip():
                    continue

                match = True
                for ck in ["type", "location", "status", "capacity", "reassign"]:
                    val = str(self._get_val_for_col(v, ck))
                    if val not in self.column_filters.get(ck, set()):
                        match = False
                        break
                
                if match:
                    chk_symbol = "☑" if vid in self.selected_ids else "☐"
                    reassign_text = "Yes" if v['auto_reassign_recurring'] else "No"
                    tree.insert("", tk.END, values=(chk_symbol, vid, v['license_number'], v['vehicle_type'], v['capacity'], v['location'], v['status'], reassign_text))

        load_filtered_tree()

        def on_table_click(event):
            region = tree.identify("region", event.x, event.y)
            if region == "cell":
                col = tree.identify_column(event.x)
                if col == "#1":
                    item = tree.identify_row(event.y)
                    if item:
                        vals = tree.item(item, "values")
                        vid = int(vals[1])
                        if vid in self.selected_ids:
                            self.selected_ids.remove(vid)
                        else:
                            self.selected_ids.add(vid)
                        load_filtered_tree()

        tree.bind("<Button-1>", on_table_click)

        btn_frame = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        btn_frame.pack(fill=tk.X, padx=30, pady=15)

        del_btn = tk.Button(btn_frame, text="Delete Selected", bg="#e74c3c", fg="white", font=(t.FONT, 9, "bold"), relief="flat", command=lambda: self.handle_delete(vehicles))
        del_btn.pack(side=tk.LEFT, padx=(0, 10), ipadx=10, ipady=6)

        maint_btn = tk.Button(btn_frame, text="Set Maintenance", bg="#f39c12", fg="white", font=(t.FONT, 9, "bold"), relief="flat", command=lambda: self.handle_status("Maintenance"))
        maint_btn.pack(side=tk.LEFT, padx=(0, 10), ipadx=10, ipady=6)

        avail_btn = tk.Button(btn_frame, text="Set Available", bg="#27ae60", fg="white", font=(t.FONT, 9, "bold"), relief="flat", command=lambda: self.handle_status("Available"))
        avail_btn.pack(side=tk.LEFT, padx=(0, 10), ipadx=10, ipady=6)

        free_btn = tk.Button(btn_frame, text="Free Up", bg="#2980b9", fg="white", font=(t.FONT, 9, "bold"), relief="flat", command=self.handle_free)
        free_btn.pack(side=tk.LEFT, ipadx=10, ipady=6)

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

    def handle_free(self):
        if not self.selected_ids:
            messagebox.showerror("Error", "Please select at least one vehicle.")
            return
        for vid in self.selected_ids:
            free_vehicle(vid)
        messagebox.showinfo("Success", "Freed up vehicle assignments.")
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

        tk.Label(popup, text=f"Filter {col_name}", font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=15, pady=(15, 10))

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
            lic_entry = tk.Entry(popup, font=(t.FONT, 10), bg=t.FIELD_BG)
            lic_entry.pack(fill=tk.X, padx=15, pady=5)
            if self.license_filter_val: lic_entry.insert(0, str(self.license_filter_val))

            def apply_filter():
                self.license_filter_val = lic_entry.get().strip()
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