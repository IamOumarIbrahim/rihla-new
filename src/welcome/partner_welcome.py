import tkinter as tk

from .users_welcome import BaseWelcomeScreen


class PartnerWelcomeScreen(BaseWelcomeScreen):
    def __init__(self, root, email):
        super().__init__(root, email, "Partner")

        # Partner-specific nav items
        self.add_nav_button("Referrals")
        self.add_nav_button("Commissions")
        self.add_nav_button("Resources")

        # Render Partner-specific scrollable content
        self.build_partner_content()

    def build_partner_content(self):
        items = [
            ("Referral Link", "Placeholder: share your unique link to earn commission on every booking.", "Copy Link"),
            ("Referrals This Month", "Placeholder: 14 clicks, 4 bookings, 1 pending payout.", "View Referrals"),
            ("Commission Statement", "Placeholder: commission earned and paid out to date.", "View Statement"),
            ("Marketing Resources", "Placeholder: banners, logos and tour descriptions you can reuse.", "Download Kit"),
        ]

        for title, description, action in items:
            card = tk.Frame(self.scrollable_frame, bg="white", bd=1, relief="solid")
            card.pack(fill=tk.X, padx=30, pady=10, ipady=15)

            tk.Label(card, text=title, font=("Arial", 14, "bold"), bg="white", fg="#2c3e50").pack(anchor="w", padx=15, pady=5)
            tk.Label(card, text=description, font=("Arial", 10), bg="white", fg="#555555",
                     wraplength=600, justify="left").pack(anchor="w", padx=15, pady=5)
            tk.Button(card, text=action, bg="#2980b9", fg="white", relief="flat").pack(anchor="w", padx=15, pady=5)


def show_partner_welcome(root, email):
    PartnerWelcomeScreen(root, email)