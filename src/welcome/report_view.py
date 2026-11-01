import tkinter as tk
from tkinter import messagebox, ttk
import theme as t
from database import create_report

# for every role: (subtitle of the page, what you can report, who its about, hint for the details box)
REPORT_OPTIONS = {
    "Customer": (
        "Something went wrong on an experience or booking? Tell the admin team.",
        ["Rude or unprofessional behaviour", "Safety concern", "Scam or fraud", "Experience not as described",
         "Payment or refund problem", "Other"],
        ["Staff member", "Vendor (event organiser)", "OTA partner", "Driver / dispatcher", "Another customer", "Other / not sure"],
        "Which event and date was it, what happened, and your booking or ticket code if you have it.",
    ),
    "Vendor": (
        "Report a problem with a customer, partner or the Rihla team.",
        ["Customer misconduct", "Fraudulent or fake booking", "Partner booking problem", "Staff problem",
         "Transport problem", "Other"],
        ["Customer", "OTA partner", "Staff member", "Driver / dispatcher", "Other"],
        "Which event and date, who was involved, and the booking or ticket code if relevant.",
    ),
    "Staff": (
        "Report an incident from check-in, an event, or a support case.",
        ["Customer misconduct", "Fake or reused ticket", "Vendor problem", "Safety concern",
         "Abusive support message", "Other"],
        ["Customer", "Vendor", "OTA partner", "Driver / dispatcher", "Other"],
        "Where and when it happened, the ticket code if scanned, and what you saw.",
    ),
    "Partner": (
        "Report a problem with a booking you made for your clients.",
        ["Booking or payment problem", "Experience not as described", "Vendor problem",
         "Unprofessional behaviour", "Client safety concern", "Other"],
        ["Vendor", "Staff member", "Driver / dispatcher", "Customer", "Other"],
        "Which booking, event and date, your client's name, and what went wrong.",
    ),
    "Dispatcher": (
        "Report a problem with vehicles, schedules or people at an event.",
        ["Vehicle misuse or damage", "Unsafe behaviour", "Vendor schedule problem", "Customer misconduct", "Other"],
        ["Vendor", "Staff member", "Customer", "OTA partner", "Other"],
        "Which vehicle (license number), event and date, and what happened.",
    ),
}


# the Report page, every role except admin has it
class ReportView:
    def __init__(self, parent_screen):
        self.root = parent_screen.root
        self.email = parent_screen.email
        self.role = parent_screen.role_name
        self.scrollable_frame = parent_screen.scrollable_frame

    def build_report_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if self.role in REPORT_OPTIONS:
            options = REPORT_OPTIONS[self.role]
        else:
            options = REPORT_OPTIONS["Customer"]
        subtitle = options[0]
        categories = options[1]
        offender_types = options[2]
        hint = options[3]

        tk.Label(self.scrollable_frame, text="Submit a Report", font=(t.FONT, 22, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(anchor="w", padx=30, pady=(20, 5))
        tk.Label(self.scrollable_frame, text=subtitle + " Reports go to the Rihla admin team only.",
                 font=(t.FONT, 11), bg=t.PAGE_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 15))

        card = tk.Frame(self.scrollable_frame, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
        card.pack(fill=tk.X, padx=30, pady=5, ipady=12, ipadx=15)
        tk.Label(card, text="REPORT DETAILS", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.PRIMARY).pack(anchor="w", padx=10, pady=(8, 8))

        row = tk.Frame(card, bg=t.CARD_BG)
        row.pack(fill=tk.X, padx=10)
        left = tk.Frame(row, bg=t.CARD_BG)
        left.pack(side=tk.LEFT, padx=(0, 20))
        right = tk.Frame(row, bg=t.CARD_BG)
        right.pack(side=tk.LEFT)

        tk.Label(left, text="What are you reporting?", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", pady=(8, 2))
        category_var = tk.StringVar(value="")
        ttk.Combobox(left, textvariable=category_var, values=categories, state="readonly", width=34, font=(t.FONT, 10)).pack(anchor="w")

        tk.Label(right, text="Who is this about?", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", pady=(8, 2))
        offender_var = tk.StringVar(value="")
        ttk.Combobox(right, textvariable=offender_var, values=offender_types, state="readonly", width=30, font=(t.FONT, 10)).pack(anchor="w")

        details = tk.Frame(card, bg=t.CARD_BG)
        details.pack(fill=tk.X, padx=10)
        tk.Label(details, text="Their email, if you know it (optional)", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", pady=(8, 2))
        offender_entry = tk.Entry(details, font=(t.FONT, 10), bg=t.FIELD_BG, relief="solid", bd=1, width=40)
        offender_entry.pack(anchor="w", ipady=3)

        tk.Label(details, text="Short summary", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", pady=(8, 2))
        subject_entry = tk.Entry(details, font=(t.FONT, 10), bg=t.FIELD_BG, relief="solid", bd=1)
        subject_entry.pack(fill=tk.X, ipady=3)

        tk.Label(details, text="What happened?", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", pady=(8, 2))
        tk.Label(details, text=hint, font=(t.FONT, 8), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w")
        description_text = tk.Text(details, font=(t.FONT, 10), bg=t.FIELD_BG, relief="solid", bd=1, height=7, wrap="word")
        description_text.pack(fill=tk.X, pady=(2, 0))

        # sends it to the server, the server checks the fields
        def submit():
            result = create_report(self.email, category_var.get(), offender_var.get(), subject_entry.get(),
                                   description_text.get("1.0", tk.END), offender_entry.get())
            if result.get("success"):
                messagebox.showinfo("Report sent", "Thank you. Your report was sent to the admin team.")
                self.build_report_content()
            else:
                messagebox.showerror("Error", result.get("message", "Could not send the report."))

        submit_btn = tk.Button(card, text="Submit Report", font=(t.FONT, 11, "bold"), bg=t.PRIMARY, fg="white",
                               relief="flat", cursor="hand2", command=submit)
        submit_btn.pack(anchor="w", padx=10, pady=(16, 4), ipadx=15, ipady=6)
        t.add_hover(submit_btn, t.PRIMARY, t.PRIMARY_HOVER)
