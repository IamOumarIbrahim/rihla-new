import tkinter as tk

from .users_welcome import BaseWelcomeScreen


class VendorWelcomeScreen(BaseWelcomeScreen):
    def __init__(self, root, email):
        super().__init__(root, email, "Vendor")

        # Vendor-specific nav items
        self.add_nav_button("My Tours")
        self.add_nav_button("Add New Tour")
        self.add_nav_button("Earnings")

        # Render Vendor-specific scrollable content
        self.build_vendor_content()

    def build_vendor_content(self):
        items = [
            ("Desert Safari Listing", "Active listing with 12 bookings this week. Dune bashing, camel rides and BBQ dinner.", "Edit Listing"),
            ("Sunset Dhow Cruise Listing", "Active listing with 7 bookings this week. Two-hour cruise with dinner on board.", "Edit Listing"),
            ("Old Town Walking Tour Listing", "Draft listing waiting for photos and pricing before it goes live.", "Finish Draft"),
            ("Monthly Earnings Summary", "Placeholder: total payouts, pending payments and platform fees will show here.", "View Report"),
        ]

        for title, description, action in items:
            card = tk.Frame(self.scrollable_frame, bg="white", bd=1, relief="solid")
            card.pack(fill=tk.X, padx=30, pady=10, ipady=15)

            tk.Label(card, text=title, font=("Arial", 14, "bold"), bg="white", fg="#2c3e50").pack(anchor="w", padx=15, pady=5)
            tk.Label(card, text=description, font=("Arial", 10), bg="white", fg="#555555",
                     wraplength=600, justify="left").pack(anchor="w", padx=15, pady=5)
            tk.Button(card, text=action, bg="#2980b9", fg="white", relief="flat").pack(anchor="w", padx=15, pady=5)


def show_vendor_welcome(root, email):
    VendorWelcomeScreen(root, email)