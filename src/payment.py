from datetime import datetime
import secrets
import tkinter as tk
from tkinter import ttk
import theme as t
from pricing import CURRENCIES, VAT_RATE, normalize_currency, vat_breakdown, format_money
from booking_pdf import save_pdf

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


def _preferred_currency(email):
    if not email:
        return "AED"
    try:
        from database import get_preferred_currency
        return normalize_currency(get_preferred_currency(email))
    except Exception:
        return "AED"


def show_demo_payment_modal(parent, title, items, total_amount, on_success, email=None):
    """items[...]["total"] and total_amount are base prices in AED, before VAT.
    on_success receives {"txn_id", "method", "currency"}."""
    base, vat, total = vat_breakdown(total_amount)

    modal = tk.Toplevel(parent)
    modal.title(f"Payment - {title}")
    modal.geometry("520x680")
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

    currency_var = tk.StringVar(value=_preferred_currency(email))

    currency_row = tk.Frame(summary_box, bg=t.FIELD_BG)
    currency_row.pack(fill=tk.X, pady=(4, 0))
    tk.Label(currency_row, text="Currency:", font=(t.FONT, 9, "bold"), bg=t.FIELD_BG, fg=t.TEXT).pack(side=tk.LEFT)
    currency_box = ttk.Combobox(currency_row, textvariable=currency_var, values=CURRENCIES, state="readonly", width=6)
    currency_box.pack(side=tk.LEFT, padx=(6, 0))

    items_frame = tk.Frame(summary_box, bg=t.FIELD_BG)
    items_frame.pack(fill=tk.X, pady=4)

    item_labels = []
    for item in items[:4]:
        lbl = tk.Label(items_frame, font=(t.FONT, 9), bg=t.FIELD_BG, fg=t.DARK_SOFT, anchor="w")
        lbl.pack(fill=tk.X)
        item_labels.append((lbl, item))

    if len(items) > 4:
        tk.Label(items_frame, text=f"... and {len(items) - 4} more events", font=(t.FONT, 8, "italic"), bg=t.FIELD_BG, fg=t.TEXT_MUTED).pack(anchor="w")

    totals = tk.Frame(summary_box, bg=t.FIELD_BG)
    totals.pack(fill=tk.X, pady=(4, 0))
    total_labels = {}
    for key, caption, font in (("base", "Base Price:", (t.FONT, 10)),
                               ("vat", f"VAT ({VAT_RATE:.0%}):", (t.FONT, 10)),
                               ("total", "Total:", (t.FONT, 13, "bold"))):
        row = tk.Frame(totals, bg=t.FIELD_BG)
        row.pack(fill=tk.X)
        colour = t.PRIMARY if key == "total" else t.TEXT
        tk.Label(row, text=caption, font=font, bg=t.FIELD_BG, fg=colour).pack(side=tk.LEFT)
        total_labels[key] = tk.Label(row, font=font, bg=t.FIELD_BG, fg=colour)
        total_labels[key].pack(side=tk.RIGHT)

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

    # Declines are shown here, inside the payment window, instead of a popup.
    error_label = tk.Label(modal, text="", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg="#c0392b",
                           wraplength=470, justify="left")
    error_label.pack(side=tk.BOTTOM, fill=tk.X, padx=20)

    def handle_submit():
        m = method_var.get()
        submitted = {"card_type": m}
        for k, ent in entries.items():
            submitted[k] = ent.get()

        ok, msg = verify_demo_payment(m, submitted)
        if not ok:
            error_label.config(text=f"Payment declined: {msg}")
            return

        payment = {
            "txn_id": f"TXN-{secrets.token_hex(4).upper()}",
            "method": {"visa": "Visa", "mastercard": "Mastercard", "bank": "Bank Transfer"}.get(m, m),
            "currency": currency_var.get(),
        }
        modal.destroy()
        if on_success:
            on_success(payment)

    pay_btn = tk.Button(btn_row, font=(t.FONT, 11, "bold"),
                        bg=t.ACCENT, fg="white", relief="flat", cursor="hand2", command=handle_submit)
    pay_btn.pack(side=tk.RIGHT, ipadx=15, ipady=6)
    t.add_hover(pay_btn, t.ACCENT, "#e67e22")

    cancel_btn = tk.Button(btn_row, text="Cancel", font=(t.FONT, 10), bg=t.CHIP_BG, fg=t.TEXT,
                           relief="flat", cursor="hand2", command=modal.destroy)
    cancel_btn.pack(side=tk.RIGHT, padx=10, ipadx=10, ipady=6)
    t.add_hover(cancel_btn, t.CHIP_BG, t.CHIP_HOVER)

    def refresh_prices(_event=None):
        cur = currency_var.get()
        for lbl, item in item_labels:
            line = f"- {item['title']} ({item['date']}) - {item['guests']} guest(s)"
            if item.get("client_name"):
                line += f" [{item['client_name']}]"
            lbl.config(text=f"{line}: {format_money(item['total'], cur)}")
        total_labels["base"].config(text=format_money(base, cur))
        total_labels["vat"].config(text=format_money(vat, cur))
        total_labels["total"].config(text=format_money(total, cur))
        pay_btn.config(text=f"Pay {format_money(total, cur)}")

    currency_box.bind("<<ComboboxSelected>>", refresh_prices)
    refresh_prices()


def _receipt_lines(entries, payment, payer_email, error):
    """Text lines (text, size, bold) shared by the window and the PDF."""
    cur = normalize_currency((payment or {}).get("currency"))
    lines = [("Rihla - Booking Details", 18, True),
             (f"Issued {datetime.now().strftime('%d %b %Y, %I:%M %p')}", 9, False), ("", 6, False)]
    if error:
        lines += [("Status: NOT CONFIRMED", 12, True), (f"Reason: {error}", 10, False),
                  ("Your payment was approved but the booking could not be saved. Please contact support.", 9, False)]
    else:
        lines.append(("Status: CONFIRMED", 12, True))
    lines += [("", 6, False), ("Payment", 13, True)]
    if payer_email:
        lines.append((f"Booked by: {payer_email}", 10, False))
    if payment:
        lines += [(f"Transaction ID: {payment['txn_id']}", 10, False),
                  (f"Payment method: {payment['method']}", 10, False),
                  (f"Currency: {cur}", 10, False)]

    grand_base = 0
    for n, e in enumerate(entries, start=1):
        base, vat, total = vat_breakdown(e["base"])
        grand_base += base
        lines += [("", 6, False), (f"Event {n}: {e['title']}" if len(entries) > 1 else e["title"], 13, True)]
        for label, value in (("Venue", e.get("venue")), ("Date", e.get("date")), ("Time", e.get("time")),
                             ("Guests", e.get("guests")), ("Group / client", e.get("client_name")),
                             ("Ticket code", e.get("ticket_code"))):
            if value:
                lines.append((f"{label}: {value}", 10, False))
        if len(entries) > 1:
            lines.append((f"Base {format_money(base, cur)}  |  VAT {format_money(vat, cur)}  |  "
                          f"Total {format_money(total, cur)}", 10, False))

    base, vat, total = vat_breakdown(grand_base)
    lines += [("", 6, False), ("Price", 13, True),
              (f"Base Price: {format_money(base, cur)}", 11, False),
              (f"VAT ({VAT_RATE:.0%}): {format_money(vat, cur)}", 11, False),
              (f"Total: {format_money(total, cur)}", 13, True)]
    if cur != "AED":
        lines.append((f"Charged in AED: {format_money(total, 'AED')}", 9, False))
    return lines


def show_booking_details_window(parent, entries, payment=None, payer_email=None, error=None, on_close=None):
    """Shows every event and booking detail after payment, with Download PDF and Close.

    entries: dicts with title, base (AED before VAT) and optional venue, date, time,
    guests, client_name, ticket_code.
    """
    lines = _receipt_lines(entries, payment, payer_email, error)

    win = tk.Toplevel(parent)
    win.title("Booking Details")
    win.geometry("560x640")
    win.transient(parent)
    win.grab_set()
    win.configure(bg=t.CARD_BG)

    header_bg = "#c0392b" if error else "#27ae60"
    header = tk.Frame(win, bg=header_bg, padx=20, pady=12)
    header.pack(fill=tk.X)
    tk.Label(header, text="Booking not completed" if error else "Booking confirmed",
             font=(t.FONT, 14, "bold"), bg=header_bg, fg="white").pack(anchor="w")

    btn_row = tk.Frame(win, bg=t.CARD_BG, padx=20, pady=12)
    btn_row.pack(fill=tk.X, side=tk.BOTTOM)
    saved_label = tk.Label(win, text="", font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED,
                           wraplength=520, justify="left")
    saved_label.pack(side=tk.BOTTOM, fill=tk.X, padx=20)

    body = tk.Frame(win, bg=t.CARD_BG, padx=20, pady=10)
    body.pack(fill=tk.BOTH, expand=True)
    text = tk.Text(body, wrap="word", relief="flat", bg=t.CARD_BG, fg=t.TEXT, font=(t.FONT, 10), padx=4, pady=4)
    scroll = tk.Scrollbar(body, orient="vertical", command=text.yview)
    text.configure(yscrollcommand=scroll.set)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    for size, bold in {(size, bold) for _, size, bold in lines}:
        text.tag_configure(f"{size}{bold}", font=(t.FONT, max(size - 2, 9), "bold" if bold else "normal"))
    for line, size, bold in lines[1:]:  # the header already names the window
        text.insert(tk.END, line + "\n", f"{size}{bold}")
    text.config(state=tk.DISABLED)

    def download_pdf():
        name = (payment or {}).get("txn_id") or datetime.now().strftime("%Y%m%d-%H%M%S")
        try:
            path = save_pdf(lines, f"Rihla_Booking_{name}.pdf")
        except OSError as exc:
            saved_label.config(text=f"Could not save the PDF: {exc}", fg="#c0392b")
            return
        saved_label.config(text=f"PDF saved to {path}", fg="#27ae60")

    def close():
        win.destroy()
        if on_close:
            on_close()

    win.protocol("WM_DELETE_WINDOW", close)

    close_btn = tk.Button(btn_row, text="Close", font=(t.FONT, 10), bg=t.CHIP_BG, fg=t.TEXT,
                          relief="flat", cursor="hand2", command=close)
    close_btn.pack(side=tk.RIGHT, ipadx=14, ipady=6)
    t.add_hover(close_btn, t.CHIP_BG, t.CHIP_HOVER)

    pdf_btn = tk.Button(btn_row, text="Download PDF", font=(t.FONT, 11, "bold"), bg=t.PRIMARY, fg="white",
                        relief="flat", cursor="hand2", command=download_pdf)
    pdf_btn.pack(side=tk.RIGHT, padx=10, ipadx=14, ipady=6)
    t.add_hover(pdf_btn, t.PRIMARY, t.PRIMARY_HOVER)
    return win
