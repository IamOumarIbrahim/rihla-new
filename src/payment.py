import secrets
import tkinter as tk
from tkinter import messagebox
import theme as t

# Hardcoded demo numbers and credentials
DEMO_PAYMENT_DETAILS = {
    "visa": {
        "card_type": "Visa",
        "card_number": "4532 0123 4567 8910",
        "cardholder": "RIHLA DEMO USER",
        "expiry": "12/28",
        "cvv": "789",
    },
    "mastercard": {
        "card_type": "Mastercard",
        "card_number": "5425 2334 4556 6778",
        "cardholder": "RIHLA DEMO USER",
        "expiry": "11/27",
        "cvv": "321",
    },
    "bank": {
        "bank_name": "Emirates NBD",
        "account_name": "Rihla Tourism LLC",
        "iban": "AE120260001234567890123",
        "swift": "EBBDAEAD",
    }
}


def normalize_card_number(num):
    return "".join(c for c in str(num) if c.isdigit())


def normalize_text(text):
    return "".join(c for c in str(text or "") if c.isalnum()).upper()


def verify_demo_payment(method, details):
    """Verifies payment against hardcoded demo records."""
    method = (method or "").strip().lower()
    if method in ("card", "visa", "mastercard"):
        card_type = details.get("card_type", "visa").lower()
        if card_type not in DEMO_PAYMENT_DETAILS:
            card_type = "visa"
        expected = DEMO_PAYMENT_DETAILS[card_type]

        entered_num = normalize_card_number(details.get("card_number", ""))
        expected_num = normalize_card_number(expected["card_number"])
        if entered_num != expected_num:
            return False, f"Card number does not match authorized demo {expected['card_type']} records."

        entered_holder = (details.get("cardholder", "")).strip().upper()
        expected_holder = expected["cardholder"].upper()
        if entered_holder != expected_holder:
            return False, "Cardholder name does not match authorized demo records."

        entered_exp = (details.get("expiry", "")).strip()
        expected_exp = expected["expiry"].strip()
        if entered_exp != expected_exp:
            return False, "Expiry date does not match authorized demo records."

        entered_cvv = (details.get("cvv", "")).strip()
        expected_cvv = expected["cvv"].strip()
        if entered_cvv != expected_cvv:
            return False, "CVV security code does not match authorized demo records."

        return True, "Payment authorized."

    elif method == "bank":
        expected = DEMO_PAYMENT_DETAILS["bank"]

        if details.get("bank_name", "").strip().lower() != expected["bank_name"].lower():
            return False, "Bank name does not match authorized demo records."

        if details.get("account_name", "").strip().lower() != expected["account_name"].lower():
            return False, "Account holder name does not match authorized demo records."

        entered_iban = normalize_text(details.get("iban", ""))
        expected_iban = normalize_text(expected["iban"])
        if entered_iban != expected_iban:
            return False, "IBAN does not match authorized demo records."

        entered_swift = normalize_text(details.get("swift", ""))
        expected_swift = normalize_text(expected["swift"])
        if entered_swift != expected_swift:
            return False, "SWIFT/BIC code does not match authorized demo records."

        return True, "Bank transfer authorized."

    return False, "Unsupported payment method."


def show_demo_payment_modal(parent, title, items, total_amount, on_success):
    modal = tk.Toplevel(parent)
    modal.title(f"Payment - {title}")
    modal.geometry("500x560")
    modal.transient(parent)
    modal.grab_set()
    modal.configure(bg=t.CARD_BG)

    # Header
    header = tk.Frame(modal, bg=t.DARK, padx=20, pady=12)
    header.pack(fill=tk.X)
    tk.Label(header, text="Payment", font=(t.FONT, 14, "bold"), bg=t.DARK, fg="white").pack(anchor="w")

    # Content container
    content = tk.Frame(modal, bg=t.CARD_BG, padx=20, pady=10)
    content.pack(fill=tk.BOTH, expand=True)

    # Order summary box
    summary_box = tk.Frame(content, bg=t.FIELD_BG, bd=1, relief="solid", highlightbackground=t.BORDER, padx=12, pady=10)
    summary_box.pack(fill=tk.X, pady=(0, 10))

    tk.Label(summary_box, text=f"Order Summary ({len(items)} event{'s' if len(items) > 1 else ''})",
             font=(t.FONT, 10, "bold"), bg=t.FIELD_BG, fg=t.TEXT).pack(anchor="w")

    items_frame = tk.Frame(summary_box, bg=t.FIELD_BG)
    items_frame.pack(fill=tk.X, pady=4)

    for item in items[:4]:
        item_line = f"- {item['title']} ({item['date']}) - {item['guests']} guest(s)"
        if item.get("client_name"):
            item_line += f" [{item['client_name']}]"
        item_line += f": {item['total']} AED"
        tk.Label(items_frame, text=item_line, font=(t.FONT, 9), bg=t.FIELD_BG, fg=t.DARK_SOFT, anchor="w").pack(fill=tk.X)

    if len(items) > 4:
        tk.Label(items_frame, text=f"... and {len(items) - 4} more events", font=(t.FONT, 8, "italic"), bg=t.FIELD_BG, fg=t.TEXT_MUTED).pack(anchor="w")

    tk.Label(summary_box, text=f"Total: {total_amount} AED", font=(t.FONT, 13, "bold"), bg=t.FIELD_BG, fg=t.PRIMARY).pack(anchor="e", pady=(4, 0))

    # Payment Method Selection
    method_var = tk.StringVar(value="visa")

    method_frame = tk.Frame(content, bg=t.CARD_BG)
    method_frame.pack(fill=tk.X, pady=(0, 10))

    methods_row = tk.Frame(method_frame, bg=t.CARD_BG)
    methods_row.pack(fill=tk.X)

    form_frame = tk.Frame(content, bg=t.CARD_BG)
    form_frame.pack(fill=tk.BOTH, expand=True)

    entries = {}

    def populate_form():
        for widget in form_frame.winfo_children():
            widget.destroy()
        entries.clear()

        m = method_var.get()
        if m in ("visa", "mastercard"):
            card_info = DEMO_PAYMENT_DETAILS[m]

            tk.Label(form_frame, text="Cardholder Name:", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", pady=(2, 1))
            name_ent = tk.Entry(form_frame, font=(t.FONT, 10), bg=t.FIELD_BG, relief="solid", bd=1)
            name_ent.pack(fill=tk.X, ipady=3, pady=(0, 6))
            name_ent.insert(0, card_info["cardholder"])
            entries["cardholder"] = name_ent

            tk.Label(form_frame, text="Card Number:", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", pady=(2, 1))
            num_ent = tk.Entry(form_frame, font=(t.FONT, 10), bg=t.FIELD_BG, relief="solid", bd=1)
            num_ent.pack(fill=tk.X, ipady=3, pady=(0, 6))
            num_ent.insert(0, card_info["card_number"])
            entries["card_number"] = num_ent

            row = tk.Frame(form_frame, bg=t.CARD_BG)
            row.pack(fill=tk.X, pady=(0, 6))

            col1 = tk.Frame(row, bg=t.CARD_BG)
            col1.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
            tk.Label(col1, text="Expiry (MM/YY):", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", pady=(2, 1))
            exp_ent = tk.Entry(col1, font=(t.FONT, 10), bg=t.FIELD_BG, relief="solid", bd=1)
            exp_ent.pack(fill=tk.X, ipady=3)
            exp_ent.insert(0, card_info["expiry"])
            entries["expiry"] = exp_ent

            col2 = tk.Frame(row, bg=t.CARD_BG)
            col2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
            tk.Label(col2, text="CVV:", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", pady=(2, 1))
            cvv_ent = tk.Entry(col2, font=(t.FONT, 10), bg=t.FIELD_BG, relief="solid", bd=1)
            cvv_ent.pack(fill=tk.X, ipady=3)
            cvv_ent.insert(0, card_info["cvv"])
            entries["cvv"] = cvv_ent

        elif m == "bank":
            bank_info = DEMO_PAYMENT_DETAILS["bank"]

            tk.Label(form_frame, text="Bank Name:", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", pady=(2, 1))
            b_ent = tk.Entry(form_frame, font=(t.FONT, 10), bg=t.FIELD_BG, relief="solid", bd=1)
            b_ent.pack(fill=tk.X, ipady=3, pady=(0, 6))
            b_ent.insert(0, bank_info["bank_name"])
            entries["bank_name"] = b_ent

            tk.Label(form_frame, text="Account Name:", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", pady=(2, 1))
            acc_ent = tk.Entry(form_frame, font=(t.FONT, 10), bg=t.FIELD_BG, relief="solid", bd=1)
            acc_ent.pack(fill=tk.X, ipady=3, pady=(0, 6))
            acc_ent.insert(0, bank_info["account_name"])
            entries["account_name"] = acc_ent

            tk.Label(form_frame, text="IBAN:", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", pady=(2, 1))
            iban_ent = tk.Entry(form_frame, font=(t.FONT, 10), bg=t.FIELD_BG, relief="solid", bd=1)
            iban_ent.pack(fill=tk.X, ipady=3, pady=(0, 6))
            iban_ent.insert(0, bank_info["iban"])
            entries["iban"] = iban_ent

            tk.Label(form_frame, text="SWIFT / BIC:", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", pady=(2, 1))
            swift_ent = tk.Entry(form_frame, font=(t.FONT, 10), bg=t.FIELD_BG, relief="solid", bd=1)
            swift_ent.pack(fill=tk.X, ipady=3, pady=(0, 6))
            swift_ent.insert(0, bank_info["swift"])
            entries["swift"] = swift_ent

        tk.Button(form_frame, text="Reset Details", font=(t.FONT, 8), bg=t.CHIP_BG, fg=t.DARK,
                  relief="flat", cursor="hand2", command=populate_form).pack(anchor="w", pady=(4, 0))

    tk.Radiobutton(methods_row, text="Visa", variable=method_var, value="visa", bg=t.CARD_BG,
                   font=(t.FONT, 9, "bold"), command=populate_form).pack(side=tk.LEFT, padx=(0, 15))
    tk.Radiobutton(methods_row, text="Mastercard", variable=method_var, value="mastercard", bg=t.CARD_BG,
                   font=(t.FONT, 9, "bold"), command=populate_form).pack(side=tk.LEFT, padx=(0, 15))
    tk.Radiobutton(methods_row, text="Bank Transfer", variable=method_var, value="bank", bg=t.CARD_BG,
                   font=(t.FONT, 9, "bold"), command=populate_form).pack(side=tk.LEFT)

    populate_form()

    # Buttons
    btn_row = tk.Frame(modal, bg=t.CARD_BG, padx=20, pady=15)
    btn_row.pack(fill=tk.X, side=tk.BOTTOM)

    def handle_submit():
        m = method_var.get()
        submitted = {"card_type": m}
        for k, ent in entries.items():
            submitted[k] = ent.get()

        ok, msg = verify_demo_payment(m, submitted)
        if not ok:
            messagebox.showerror("Payment Failed", f"Payment Declined:\n{msg}", parent=modal)
            return

        txn_id = f"TXN-{secrets.token_hex(4).upper()}"
        messagebox.showinfo("Payment Successful", f"Payment of {total_amount} AED approved.\n\nTransaction ID: {txn_id}", parent=modal)
        modal.destroy()
        if on_success:
            on_success()

    pay_btn = tk.Button(btn_row, text=f"Pay {total_amount} AED", font=(t.FONT, 11, "bold"),
                        bg=t.ACCENT, fg="white", relief="flat", cursor="hand2", command=handle_submit)
    pay_btn.pack(side=tk.RIGHT, ipadx=15, ipady=6)
    t.add_hover(pay_btn, t.ACCENT, "#e67e22")

    cancel_btn = tk.Button(btn_row, text="Cancel", font=(t.FONT, 10), bg=t.CHIP_BG, fg=t.TEXT,
                           relief="flat", cursor="hand2", command=modal.destroy)
    cancel_btn.pack(side=tk.RIGHT, padx=10, ipadx=10, ipady=6)
    t.add_hover(cancel_btn, t.CHIP_BG, t.CHIP_HOVER)
