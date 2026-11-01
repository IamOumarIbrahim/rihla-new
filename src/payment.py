from datetime import datetime
import secrets
import tkinter as tk
from tkinter import ttk
import theme as t
from pricing import CURRENCIES, VAT_RATE, normalize_currency, vat_breakdown, format_money
from booking_pdf import save_pdf

# demo card and bank details (hardcoded, its only a demo)
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

# "5%" for the VAT labels
VAT_TEXT = str(int(round(VAT_RATE * 100))) + "%"


# keeps only the digits
def normalize_card_number(num):
    result = ""
    for c in str(num):
        if c.isdigit():
            result = result + c
    return result


# keeps only letters and numbers, in capitals
def normalize_text(text):
    if not text:
        text = ""
    result = ""
    for c in str(text):
        if c.isalnum():
            result = result + c
    return result.upper()


# checks the payment against the demo details above
def verify_demo_payment(method, details):
    method = (method or "").strip().lower()
    if method in ("card", "visa", "mastercard"):
        card_type = details.get("card_type", "visa").lower()
        if card_type not in DEMO_PAYMENT_DETAILS:
            card_type = "visa"
        expected = DEMO_PAYMENT_DETAILS[card_type]

        entered_num = normalize_card_number(details.get("card_number", ""))
        expected_num = normalize_card_number(expected["card_number"])
        if entered_num != expected_num:
            return False, "Card number does not match authorized demo " + expected["card_type"] + " records."

        entered_holder = details.get("cardholder", "").strip().upper()
        expected_holder = expected["cardholder"].upper()
        if entered_holder != expected_holder:
            return False, "Cardholder name does not match authorized demo records."

        entered_exp = details.get("expiry", "").strip()
        expected_exp = expected["expiry"].strip()
        if entered_exp != expected_exp:
            return False, "Expiry date does not match authorized demo records."

        entered_cvv = details.get("cvv", "").strip()
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


# the item totals and total_amount are prices in AED without VAT
# on_success gets {"txn_id", "method", "currency"}
def show_demo_payment_modal(parent, title, items, total_amount, on_success, email=None):
    base, vat, total = vat_breakdown(total_amount)

    modal = tk.Toplevel(parent)
    modal.title("Payment - " + title)
    modal.geometry("520x680")
    modal.transient(parent)
    modal.grab_set()
    modal.configure(bg=t.CARD_BG)

    header = tk.Frame(modal, bg=t.DARK, padx=20, pady=12)
    header.pack(fill=tk.X)
    tk.Label(header, text="Payment", font=(t.FONT, 14, "bold"), bg=t.DARK, fg="white").pack(anchor="w")

    content = tk.Frame(modal, bg=t.CARD_BG, padx=20, pady=10)
    content.pack(fill=tk.BOTH, expand=True)

    # Order summary
    summary_box = tk.Frame(content, bg=t.FIELD_BG, bd=1, relief="solid", highlightbackground=t.BORDER, padx=12, pady=10)
    summary_box.pack(fill=tk.X, pady=(0, 10))

    if len(items) > 1:
        plural = "s"
    else:
        plural = ""
    tk.Label(summary_box, text="Order Summary (" + str(len(items)) + " event" + plural + ")",
             font=(t.FONT, 10, "bold"), bg=t.FIELD_BG, fg=t.TEXT).pack(anchor="w")

    currency_var = tk.StringVar(value=_preferred_currency(email))

    currency_row = tk.Frame(summary_box, bg=t.FIELD_BG)
    currency_row.pack(fill=tk.X, pady=(4, 0))
    tk.Label(currency_row, text="Currency:", font=(t.FONT, 9, "bold"), bg=t.FIELD_BG, fg=t.TEXT).pack(side=tk.LEFT)
    currency_box = ttk.Combobox(currency_row, textvariable=currency_var, values=CURRENCIES, state="readonly", width=6)
    currency_box.pack(side=tk.LEFT, padx=(6, 0))

    items_frame = tk.Frame(summary_box, bg=t.FIELD_BG)
    items_frame.pack(fill=tk.X, pady=4)

    # only the first 4 items are shown
    item_labels = []
    for item in items[:4]:
        lbl = tk.Label(items_frame, font=(t.FONT, 9), bg=t.FIELD_BG, fg=t.DARK_SOFT, anchor="w")
        lbl.pack(fill=tk.X)
        item_labels.append((lbl, item))

    if len(items) > 4:
        tk.Label(items_frame, text="... and " + str(len(items) - 4) + " more events", font=(t.FONT, 8, "italic"), bg=t.FIELD_BG, fg=t.TEXT_MUTED).pack(anchor="w")

    # base price, vat and total rows
    totals = tk.Frame(summary_box, bg=t.FIELD_BG)
    totals.pack(fill=tk.X, pady=(4, 0))
    total_labels = {}

    row = tk.Frame(totals, bg=t.FIELD_BG)
    row.pack(fill=tk.X)
    tk.Label(row, text="Base Price:", font=(t.FONT, 10), bg=t.FIELD_BG, fg=t.TEXT).pack(side=tk.LEFT)
    total_labels["base"] = tk.Label(row, font=(t.FONT, 10), bg=t.FIELD_BG, fg=t.TEXT)
    total_labels["base"].pack(side=tk.RIGHT)

    row = tk.Frame(totals, bg=t.FIELD_BG)
    row.pack(fill=tk.X)
    tk.Label(row, text="VAT (" + VAT_TEXT + "):", font=(t.FONT, 10), bg=t.FIELD_BG, fg=t.TEXT).pack(side=tk.LEFT)
    total_labels["vat"] = tk.Label(row, font=(t.FONT, 10), bg=t.FIELD_BG, fg=t.TEXT)
    total_labels["vat"].pack(side=tk.RIGHT)

    row = tk.Frame(totals, bg=t.FIELD_BG)
    row.pack(fill=tk.X)
    tk.Label(row, text="Total:", font=(t.FONT, 13, "bold"), bg=t.FIELD_BG, fg=t.PRIMARY).pack(side=tk.LEFT)
    total_labels["total"] = tk.Label(row, font=(t.FONT, 13, "bold"), bg=t.FIELD_BG, fg=t.PRIMARY)
    total_labels["total"].pack(side=tk.RIGHT)

    # Payment method
    method_var = tk.StringVar(value="visa")

    method_frame = tk.Frame(content, bg=t.CARD_BG)
    method_frame.pack(fill=tk.X, pady=(0, 10))

    methods_row = tk.Frame(method_frame, bg=t.CARD_BG)
    methods_row.pack(fill=tk.X)

    form_frame = tk.Frame(content, bg=t.CARD_BG)
    form_frame.pack(fill=tk.BOTH, expand=True)

    entries = {}

    # fills the form with the demo details of the method that is picked
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

    # if the payment is declined the message shows here in the window and not in a popup
    error_label = tk.Label(modal, text="", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg="#c0392b",
                           wraplength=470, justify="left")
    error_label.pack(side=tk.BOTTOM, fill=tk.X, padx=20)

    def handle_submit():
        m = method_var.get()
        submitted = {"card_type": m}
        for k in entries:
            submitted[k] = entries[k].get()

        ok, msg = verify_demo_payment(m, submitted)
        if not ok:
            error_label.config(text="Payment declined: " + msg)
            return

        if m == "visa":
            method_name = "Visa"
        elif m == "mastercard":
            method_name = "Mastercard"
        elif m == "bank":
            method_name = "Bank Transfer"
        else:
            method_name = m
        payment = {
            "txn_id": "TXN-" + secrets.token_hex(4).upper(),
            "method": method_name,
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

    # writes all the prices again in the currency that is picked
    def refresh_prices(event=None):
        cur = currency_var.get()
        for lbl, item in item_labels:
            line = "- " + str(item["title"]) + " (" + str(item["date"]) + ") - " + str(item["guests"]) + " guest(s)"
            if item.get("client_name"):
                line += " [" + str(item["client_name"]) + "]"
            lbl.config(text=line + ": " + format_money(item["total"], cur))
        total_labels["base"].config(text=format_money(base, cur))
        total_labels["vat"].config(text=format_money(vat, cur))
        total_labels["total"].config(text=format_money(total, cur))
        pay_btn.config(text="Pay " + format_money(total, cur))

    currency_box.bind("<<ComboboxSelected>>", refresh_prices)
    refresh_prices()


# the lines (text, size, bold) for the window and for the pdf
def _receipt_lines(entries, payment, payer_email, error):
    if payment:
        cur = normalize_currency(payment.get("currency"))
    else:
        cur = normalize_currency(None)
    lines = []
    lines.append(("Rihla - Booking Details", 18, True))
    lines.append(("Issued " + datetime.now().strftime('%d %b %Y, %I:%M %p'), 9, False))
    lines.append(("", 6, False))
    if error:
        lines.append(("Status: NOT CONFIRMED", 12, True))
        lines.append(("Reason: " + str(error), 10, False))
        lines.append(("Your payment was approved but the booking could not be saved. Please contact support.", 9, False))
    else:
        lines.append(("Status: CONFIRMED", 12, True))
    lines.append(("", 6, False))
    lines.append(("Payment", 13, True))
    if payer_email:
        lines.append(("Booked by: " + str(payer_email), 10, False))
    if payment:
        lines.append(("Transaction ID: " + str(payment["txn_id"]), 10, False))
        lines.append(("Payment method: " + str(payment["method"]), 10, False))
        lines.append(("Currency: " + cur, 10, False))

    grand_base = 0
    n = 1
    for e in entries:
        base, vat, total = vat_breakdown(e["base"])
        grand_base += base
        lines.append(("", 6, False))
        if len(entries) > 1:
            lines.append(("Event " + str(n) + ": " + str(e["title"]), 13, True))
        else:
            lines.append((e["title"], 13, True))

        # only the details that have a value
        if e.get("venue"):
            lines.append(("Venue: " + str(e.get("venue")), 10, False))
        if e.get("date"):
            lines.append(("Date: " + str(e.get("date")), 10, False))
        if e.get("time"):
            lines.append(("Time: " + str(e.get("time")), 10, False))
        if e.get("guests"):
            lines.append(("Guests: " + str(e.get("guests")), 10, False))
        if e.get("client_name"):
            lines.append(("Group / client: " + str(e.get("client_name")), 10, False))
        if e.get("ticket_code"):
            lines.append(("Ticket code: " + str(e.get("ticket_code")), 10, False))

        if len(entries) > 1:
            lines.append(("Base " + format_money(base, cur) + "  |  VAT " + format_money(vat, cur) + "  |  "
                          + "Total " + format_money(total, cur), 10, False))
        n += 1

    base, vat, total = vat_breakdown(grand_base)
    lines.append(("", 6, False))
    lines.append(("Price", 13, True))
    lines.append(("Base Price: " + format_money(base, cur), 11, False))
    lines.append(("VAT (" + VAT_TEXT + "): " + format_money(vat, cur), 11, False))
    lines.append(("Total: " + format_money(total, cur), 13, True))
    if cur != "AED":
        lines.append(("Charged in AED: " + format_money(total, 'AED'), 9, False))
    return lines


# window after the payment with all the event and booking details, Download PDF and Close
# entries are dicts with title, base (AED without VAT) and maybe venue, date, time,
# guests, client_name, ticket_code
def show_booking_details_window(parent, entries, payment=None, payer_email=None, error=None, on_close=None):
    lines = _receipt_lines(entries, payment, payer_email, error)

    win = tk.Toplevel(parent)
    win.title("Booking Details")
    win.geometry("560x640")
    win.transient(parent)
    win.grab_set()
    win.configure(bg=t.CARD_BG)

    if error:
        header_bg = "#c0392b"
        header_text = "Booking not completed"
    else:
        header_bg = "#27ae60"
        header_text = "Booking confirmed"
    header = tk.Frame(win, bg=header_bg, padx=20, pady=12)
    header.pack(fill=tk.X)
    tk.Label(header, text=header_text,
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

    # one text tag for every (size, bold) that is used, a bit smaller than in the pdf
    done_tags = []
    for line, size, bold in lines:
        tag = str(size) + str(bold)
        if tag not in done_tags:
            done_tags.append(tag)
            tag_size = size - 2
            if tag_size < 9:
                tag_size = 9
            if bold:
                weight = "bold"
            else:
                weight = "normal"
            text.tag_configure(tag, font=(t.FONT, tag_size, weight))
    for line, size, bold in lines[1:]:  # the header already has the title
        text.insert(tk.END, line + "\n", str(size) + str(bold))
    text.config(state=tk.DISABLED)

    def download_pdf():
        name = None
        if payment:
            name = payment.get("txn_id")
        if not name:
            name = datetime.now().strftime("%Y%m%d-%H%M%S")
        try:
            path = save_pdf(lines, "Rihla_Booking_" + str(name) + ".pdf")
        except OSError as exc:
            saved_label.config(text="Could not save the PDF: " + str(exc), fg="#c0392b")
            return
        saved_label.config(text="PDF saved to " + path, fg="#27ae60")

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
