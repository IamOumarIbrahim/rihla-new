import tkinter as tk

from .users_welcome import BaseWelcomeScreen


class StaffWelcomeScreen(BaseWelcomeScreen):
    def __init__(self, root, email):
        super().__init__(root, email, "Staff")

        # Staff-specific nav items
        self.add_nav_button("Bookings")
        self.add_nav_button("Support Tickets")
        self.add_nav_button("Schedule")

        # Render Staff-specific scrollable content
        self.build_staff_content()

    def build_staff_content(self):
        items = [
            ("Pending Booking Approvals", "Placeholder: 5 bookings are waiting for confirmation.", "Review Bookings"),
            ("Open Support Tickets", "Placeholder: 3 customer tickets need a reply today.", "Open Tickets"),
            ("Team Schedule", "Placeholder: shifts and assignments for this week.", "View Schedule"),
            ("Customer Lookup", "Placeholder: search customers by email or booking number.", "Search"),
        ]

        for title, description, action in items:
            card = tk.Frame(self.scrollable_frame, bg="white", bd=1, relief="solid")
            card.pack(fill=tk.X, padx=30, pady=10, ipady=15)

            tk.Label(card, text=title, font=("Arial", 14, "bold"), bg="white", fg="#2c3e50").pack(anchor="w", padx=15, pady=5)
            tk.Label(card, text=description, font=("Arial", 10), bg="white", fg="#555555",
                     wraplength=600, justify="left").pack(anchor="w", padx=15, pady=5)
            tk.Button(card, text=action, bg="#2980b9", fg="white", relief="flat").pack(anchor="w", padx=15, pady=5)


def show_staff_welcome(root, email):
    StaffWelcomeScreen(root, email)