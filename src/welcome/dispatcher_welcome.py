import tkinter as tk

from .users_welcome import BaseWelcomeScreen


class DispatcherWelcomeScreen(BaseWelcomeScreen):
    def __init__(self, root, email):
        super().__init__(root, email, "Dispatcher")

        # Dispatcher-specific nav items
        self.add_nav_button("Trips Today")
        self.add_nav_button("Drivers")
        self.add_nav_button("Vehicles")

        # Render Dispatcher-specific scrollable content
        self.build_dispatcher_content()

    def build_dispatcher_content(self):
        items = [
            ("Trips Today", "Placeholder: 8 pickups scheduled, 2 not yet assigned to a driver.", "View Trips"),
            ("Driver Availability", "Placeholder: 6 drivers on duty, 2 off shift.", "Manage Drivers"),
            ("Vehicle Status", "Placeholder: 5 vehicles ready, 1 in maintenance.", "View Vehicles"),
            ("Unassigned Pickups", "Placeholder: assign a driver and vehicle to each open pickup.", "Assign Now"),
        ]

        for title, description, action in items:
            card = tk.Frame(self.scrollable_frame, bg="white", bd=1, relief="solid")
            card.pack(fill=tk.X, padx=30, pady=10, ipady=15)

            tk.Label(card, text=title, font=("Arial", 14, "bold"), bg="white", fg="#2c3e50").pack(anchor="w", padx=15, pady=5)
            tk.Label(card, text=description, font=("Arial", 10), bg="white", fg="#555555",
                     wraplength=600, justify="left").pack(anchor="w", padx=15, pady=5)
            tk.Button(card, text=action, bg="#2980b9", fg="white", relief="flat").pack(anchor="w", padx=15, pady=5)


def show_dispatcher_welcome(root, email):
    DispatcherWelcomeScreen(root, email)