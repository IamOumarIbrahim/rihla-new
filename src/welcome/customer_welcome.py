import tkinter as tk
from tkinter import messagebox
from .users_welcome import BaseWelcomeScreen
from screens.event_screen import show_event_screen
import theme as t


class CustomerWelcomeScreen(BaseWelcomeScreen):
    def __init__(self, root, email):
        super().__init__(root, email, "Customer")
        self.root = root

        # Add Customer-specific nav items
        self.add_nav_button("My Bookings")
        self.add_nav_button("Explore Tours")
        self.add_nav_button("Live Chat")

        # Extended tour data matching filter criteria
        self.all_tours = [
            {
                "title": "Red Dune Sunset Safari and Royal BBQ Dinner",
                "category": "Evening Safari",
                "price": 240,
                "time": "Afternoon / Sunset (15:00)",
                "level": "Extreme Dune Bashing",
                "rating": "5.0 ★★★★★",
                "desc": "Experience dune bashing, camel rides, and traditional buffet dinners under the desert stars."
            },
            {
                "title": "Morning Dune Bashing Adventure",
                "category": "Morning Dune Bashing",
                "price": "180",
                "time": "Morning (08:00)",
                "level": "Extreme Dune Bashing",
                "rating": "4.8 ★★★★☆",
                "desc": "Catch the early morning desert sunrise with high-speed dune driving and sandboarding."
            },
            {
                "title": "Overnight Desert Camping Experience",
                "category": "Overnight Camp",
                "price": 450,
                "time": "Overnight",
                "level": "Gentle / Family Friendly",
                "rating": "4.9 ★★★★★",
                "desc": "Sleep under the clear desert sky with stargazing, campfire storytelling, and breakfast."
            },
            {
                "title": "Marina Dhow Cruise Dinner",
                "category": "Dhow Cruise",
                "price": 200,
                "time": "Afternoon / Sunset (15:00)",
                "level": "Gentle / Family Friendly",
                "rating": "4.7 ★★★★☆",
                "desc": "Enjoy a luxury dinner cruise with live entertainment along the illuminated coastline."
            }
        ]

        # Active filter states with multi-selection support for checkboxes
        self.current_filters = {
            "category": "All Experiences",
            "max_price": 600,
            "times": [],
            "levels": []
        }

        self.build_customer_content(self.all_tours)

    def build_customer_content(self, tours_to_show):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        tk.Label(self.scrollable_frame, text=f"Marhaba, {self.email.split('@')[0].capitalize()}", font=(t.FONT, 18, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 10))

        # Search Bar & Filter Button Frame
        search_frame = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        search_frame.pack(fill=tk.X, padx=30, pady=10)
        
        tk.Label(search_frame, text="🔍", font=(t.FONT, 12), bg=t.PAGE_BG).pack(side=tk.LEFT, padx=(0, 5))
        
        self.search_entry = tk.Entry(search_frame, font=(t.FONT, 11))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, ipady=5)
        self.search_entry.insert(0, "Search safaris, yacht charters...")
        self.search_entry.bind("<FocusIn>", lambda e: self.search_entry.delete(0, tk.END) if self.search_entry.get() == "Search safaris, yacht charters..." else None)
        
        search_btn = tk.Button(search_frame, text="Search", bg=t.ACCENT, fg="white", font=(t.FONT, 10, "bold"), relief="flat", command=self.filter_tours)
        search_btn.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=3)
        t.add_hover(search_btn, t.ACCENT, "#e67e22")

        filter_btn = tk.Button(search_frame, text="⚙️ Filter", bg=t.DARK_SOFT, fg="white", font=(t.FONT, 10, "bold"), relief="flat", command=self.open_filter_modal)
        filter_btn.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=3)
        t.add_hover(filter_btn, t.DARK_SOFT, t.DARK)

        # Category Filter Buttons
        cat_frame = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        cat_frame.pack(fill=tk.X, padx=30, pady=10)
        
        categories = ["All Experiences", "Evening Safari", "Morning Dune Bashing", "Overnight Camp", "Dhow Cruise"]
        for cat in categories:
            is_active = self.current_filters["category"] == cat
            btn_bg = t.ACCENT if is_active else t.CHIP_BG
            btn_fg = "white" if is_active else t.TEXT
            tk.Button(cat_frame, text=cat, bg=btn_bg, fg=btn_fg, font=(t.FONT, 9, "bold" if is_active else "normal"), relief="flat",
                      command=lambda c=cat: self.filter_by_category(c)).pack(side=tk.LEFT, padx=4, ipady=4, ipadx=8)

        tk.Label(self.scrollable_frame, text=f"Featured Excursions ({len(tours_to_show)} Available)", font=(t.FONT, 14, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 5))

        # Render Tour Cards in a Grid (2 columns)
        grid_container = tk.Frame(self.scrollable_frame, bg=t.PAGE_BG)
        grid_container.pack(fill=tk.X, padx=30, pady=10)
        grid_container.columnconfigure(0, weight=1, uniform="col")
        grid_container.columnconfigure(1, weight=1, uniform="col")

        for i, tour in enumerate(tours_to_show):
            row = i // 2
            col = i % 2

            card = tk.Frame(grid_container, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
            card.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)

            top_row = tk.Frame(card, bg=t.CARD_BG)
            top_row.pack(fill=tk.X, padx=15, pady=10)
            tk.Label(top_row, text=tour["rating"], font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.ACCENT).pack(side=tk.LEFT)
            price_display = f"{tour['price']} AED" if isinstance(tour['price'], int) else tour['price']
            tk.Label(top_row, text=f"From {price_display}", font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.ACCENT).pack(side=tk.RIGHT)

            tk.Label(card, text=tour["title"], font=(t.FONT, 13, "bold"), bg=t.CARD_BG, fg=t.TEXT, wraplength=280, justify="left").pack(anchor="w", padx=15, pady=2)
            tk.Label(card, text=tour["desc"], font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED, wraplength=280, justify="left").pack(anchor="w", padx=15, pady=6)
            
            details_btn = tk.Button(card, text="View Details", bg=t.PRIMARY, fg="white", font=(t.FONT, 10, "bold"), relief="flat", 
                                    command=lambda t=tour: show_event_screen(self.root, self.email, t))
            details_btn.pack(anchor="w", padx=15, pady=(5, 15), ipadx=10, ipady=5)
            t.add_hover(details_btn, t.PRIMARY, t.PRIMARY_HOVER)

    def open_filter_modal(self):
        modal = tk.Toplevel(self.root)
        modal.title("Filter Excursions")
        modal.geometry("440x580")
        modal.configure(bg=t.CARD_BG)
        modal.resizable(False, False)

        # Center the modal relative to root
        modal.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (440 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (580 // 2)
        modal.geometry(f"+{x}+{y}")

        tk.Label(modal, text="Filter Excursions", font=(t.FONT, 18, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 10))

        content_frame = tk.Frame(modal, bg=t.CARD_BG)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=5)

        # Price Range Slider
        tk.Label(content_frame, text="Price Range (AED)", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(5, 5))
        
        price_slider = tk.Scale(content_frame, from_=150, to=600, orient=tk.HORIZONTAL, bg=t.FIELD_BG, fg=t.TEXT, font=(t.FONT, 9), highlightthickness=1, highlightbackground=t.BORDER, troughcolor=t.BORDER)
        price_slider.set(self.current_filters["max_price"])
        price_slider.pack(fill=tk.X, pady=5)

        # Departure Time Checkboxes
        tk.Label(content_frame, text="Departure Time", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(15, 5))
        
        time_vars = {}
        times = ["Morning (08:00)", "Afternoon / Sunset (15:00)", "Overnight"]
        for t_val in times:
            var = tk.BooleanVar(value=t_val in self.current_filters["times"])
            time_vars[t_val] = var
            cb = tk.Checkbutton(content_frame, text=t_val, variable=var, font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT, activebackground=t.CARD_BG, activeforeground=t.TEXT, selectcolor=t.CARD_BG)
            cb.pack(anchor="w", pady=2)

        # Adventure Level Checkboxes
        tk.Label(content_frame, text="Vehicle and Adventure Level", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(15, 5))
        
        level_vars = {}
        levels = ["Extreme Dune Bashing", "Gentle / Family Friendly", "Private 4x4", "Quad Bike Included"]
        for l_val in levels:
            var = tk.BooleanVar(value=l_val in self.current_filters["levels"])
            level_vars[l_val] = var
            cb = tk.Checkbutton(content_frame, text=l_val, variable=var, font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT, activebackground=t.CARD_BG, activeforeground=t.TEXT, selectcolor=t.CARD_BG)
            cb.pack(anchor="w", pady=2)

        # Apply & Reset Buttons
        btn_frame = tk.Frame(modal, bg=t.CARD_BG)
        btn_frame.pack(fill=tk.X, padx=30, pady=20)

        def apply_filters():
            self.current_filters["max_price"] = price_slider.get()
            self.current_filters["times"] = [t_val for t_val, var in time_vars.items() if var.get()]
            self.current_filters["levels"] = [l_val for l_val, var in level_vars.items() if var.get()]
            modal.destroy()
            self.apply_all_filters()

        def reset_filters():
            price_slider.set(600)
            for var in time_vars.values():
                var.set(False)
            for var in level_vars.values():
                var.set(False)
            self.current_filters = {"category": "All Experiences", "max_price": 600, "times": [], "levels": []}
            modal.destroy()
            self.apply_all_filters()

        reset_btn = tk.Button(btn_frame, text="Reset", font=(t.FONT, 10, "bold"), bg=t.CHIP_BG, fg=t.TEXT, relief="flat", command=reset_filters)
        reset_btn.pack(side=tk.LEFT, ipadx=15, ipady=8)
        t.add_hover(reset_btn, t.CHIP_BG, t.CHIP_HOVER)

        apply_btn = tk.Button(btn_frame, text="Apply Filters", font=(t.FONT, 10, "bold"), bg=t.PRIMARY, fg="white", relief="flat", command=apply_filters)
        apply_btn.pack(side=tk.RIGHT, ipadx=20, ipady=8)
        t.add_hover(apply_btn, t.PRIMARY, t.PRIMARY_HOVER)

    def apply_all_filters(self):
        filtered = self.all_tours
        
        # Category Filter
        cat = self.current_filters["category"]
        if cat != "All Experiences":
            filtered = [t for t in filtered if t["category"] == cat]

        # Price Filter
        max_p = self.current_filters["max_price"]
        filtered = [t for t in filtered if int(str(t["price"]).replace(" AED", "")) <= max_p]

        # Time Filter (multi-select checkboxes)
        selected_times = self.current_filters["times"]
        if selected_times:
            filtered = [t for t in filtered if t.get("time") in selected_times]

        # Level Filter (multi-select checkboxes)
        selected_levels = self.current_filters["levels"]
        if selected_levels:
            filtered = [t for t in filtered if t.get("level") in selected_levels]

        self.build_customer_content(filtered)

    def filter_tours(self):
        query = self.search_entry.get().lower().strip()
        if not query or query == "search safaris, yacht charters...":
            filtered = self.all_tours
        else:
            filtered = [t for t in self.all_tours if query in t["title"].lower() or query in t["category"].lower()]
        self.build_customer_content(filtered)

    def filter_by_category(self, category):
        self.current_filters["category"] = category
        self.apply_all_filters()


def show_customer_welcome(root, email):
    CustomerWelcomeScreen(root, email)