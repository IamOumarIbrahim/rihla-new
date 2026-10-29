import tkinter as tk

from .users_welcome import BaseWelcomeScreen


class CustomerWelcomeScreen(BaseWelcomeScreen):
    def __init__(self, root, email):
        super().__init__(root, email, "Customer")

        # Add Customer-specific nav items
        self.add_nav_button("My Bookings")
        self.add_nav_button("Explore Tours")

        # Render Customer-specific scrollable content
        self.build_customer_content()

    def build_customer_content(self):
        for i in range(1, 10):
            card = tk.Frame(self.scrollable_frame, bg="white", bd=1, relief="solid")
            card.pack(fill=tk.X, padx=30, pady=10, ipady=15)

            tk.Label(card, text=f"Tour Package Option #{i}", font=("Arial", 14, "bold"), bg="white", fg="#2c3e50").pack(anchor="w", padx=15, pady=5)
            tk.Label(card, text=f"Experience dune bashing, camel rides, and traditional buffet dinners under the desert stars for Option #{i}.",
                     font=("Arial", 10), bg="white", fg="#555555", wraplength=600, justify="left").pack(anchor="w", padx=15, pady=5)
            tk.Button(card, text="Book Now", bg="#27ae60", fg="white", relief="flat").pack(anchor="w", padx=15, pady=5)


def show_customer_welcome(root, email):
    CustomerWelcomeScreen(root, email)