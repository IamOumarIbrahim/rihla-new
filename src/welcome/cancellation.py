"""Shared bits for cancelling bookings: policy and refund text, the reason dialog, and a page header with Refresh.

Policy (checked again by the server): customers and partners get a full refund 48 hours or more
before the event, half from 48 to 24 hours, and cannot cancel in the last 24 hours.
A vendor or admin cancelling always refunds in full, VAT included.
"""
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

import theme as t
from pricing import refund_breakdown

FULL_REFUND_HOURS = 48
HALF_REFUND_HOURS = 24
WHO = {"Vendor": "the vendor", "Admin": "Rihla support"}


def _when(text):
    try:
        return datetime.strptime((text or "")[:16], "%Y-%m-%d %H:%M").strftime("%d %b %Y, %H:%M")
    except ValueError:
        return text or ""


def refund_text(total, percent):
    base, vat, refund = refund_breakdown(total, percent)
    return f"{refund:,.2f} AED ({percent}%: {base:,.2f} + {vat:,.2f} VAT)"


def policy_line(booking):
    """One line under a confirmed booking that says what cancelling now would give back."""
    percent = booking.get("refund_if_cancelled")
    if percent == 100:
        return f"Free cancellation until {FULL_REFUND_HOURS} hours before the start."
    if percent == 50:
        return f"Cancelling now refunds 50%. Cancellation closes {HALF_REFUND_HOURS} hours before the start."
    return f"Cancellation closed: it is less than {HALF_REFUND_HOURS} hours before the start."


def cancelled_line(booking, viewer_email=None):
    """'Cancelled 31 Oct 2026, 14:02 by the vendor: reason. Refunded 756.00 AED (100%: ...)'."""
    role = booking.get("cancelled_by_role")
    by = booking.get("cancelled_by") or ""
    if viewer_email and by.lower() == viewer_email.lower():
        who = "you"
    else:
        who = WHO.get(role, by or "the booker")
    text = "Cancelled"
    if booking.get("cancelled_at"):
        text += f" {_when(booking['cancelled_at'])}"
    text += f" by {who}"
    if booking.get("cancel_reason"):
        text += f": {booking['cancel_reason']}"
    if booking.get("refund_percent") is not None:
        text += f". Refunded {refund_text(booking['total_price'], booking['refund_percent'])}."
    return text


def confirm_own_cancel(booking):
    """Asks the booker to confirm, showing the refund they will get. True when they say yes."""
    percent = booking.get("refund_if_cancelled")
    if percent is None:
        messagebox.showinfo("Cannot cancel", policy_line(booking))
        return False
    return messagebox.askyesno(
        "Cancel booking",
        f"Cancel your booking for {booking['event_title']}?\n\n"
        f"Refund: {refund_text(booking['total_price'], percent)}\n"
        "The ticket code will stop working.",
    )


def ask_reason(parent, booking):
    """Reason dialog for a vendor or admin cancelling someone else's booking. Returns the reason, or None."""
    win = tk.Toplevel(parent)
    win.title("Cancel booking")
    win.configure(bg=t.CARD_BG)
    win.resizable(False, False)
    win.transient(parent)
    win.grab_set()

    tk.Label(win, text=f"Cancel {booking['customer_email']}'s booking", font=(t.FONT, 13, "bold"),
             bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=20, pady=(16, 2))
    tk.Label(win, text=f"{booking['event_title']}  |  {booking['booking_date']}  |  {booking['guests']} guest(s)",
             font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=20)
    tk.Label(win, text=f"Full refund: {refund_text(booking['total_price'], 100)}", font=(t.FONT, 10, "bold"),
             bg=t.CARD_BG, fg="#27ae60").pack(anchor="w", padx=20, pady=(8, 8))
    tk.Label(win, text="Reason (the customer will see it)", font=(t.FONT, 9, "bold"),
             bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=20)
    box = tk.Text(win, width=48, height=4, font=(t.FONT, 10), wrap="word")
    box.pack(padx=20, pady=(2, 10))
    box.focus_set()

    result = {"reason": None}

    def confirm():
        reason = box.get("1.0", tk.END).strip()
        if not reason:
            messagebox.showerror("Reason needed", "Please give the customer a reason.", parent=win)
            return
        result["reason"] = reason
        win.destroy()

    btns = tk.Frame(win, bg=t.CARD_BG)
    btns.pack(fill=tk.X, padx=20, pady=(0, 16))
    tk.Button(btns, text="Cancel booking and refund", font=(t.FONT, 10, "bold"), bg="#e74c3c", fg="white",
              relief="flat", cursor="hand2", command=confirm).pack(side=tk.LEFT, ipadx=10, ipady=5)
    tk.Button(btns, text="Keep booking", font=(t.FONT, 10), bg=t.CHIP_BG, fg=t.TEXT, relief="flat",
              cursor="hand2", command=win.destroy).pack(side=tk.LEFT, padx=8, ipadx=10, ipady=5)
    win.bind("<Escape>", lambda e: win.destroy())
    parent.wait_window(win)
    return result["reason"]


def page_header(parent, title, on_refresh, pady=(20, 5)):
    """Page title with a Refresh button on the right, for pages that show other people's changes."""
    row = tk.Frame(parent, bg=t.PAGE_BG)
    row.pack(fill=tk.X, padx=30, pady=pady)
    tk.Label(row, text=title, font=(t.FONT, 22, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(side=tk.LEFT)
    btn = tk.Button(row, text="Refresh", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT, relief="solid", bd=1,
                    cursor="hand2", command=on_refresh)
    btn.pack(side=tk.RIGHT, ipadx=10, ipady=3)
    t.add_hover(btn, t.CARD_BG, t.CHIP_HOVER)
    return row


def cancel_button(parent):
    """Red 'Cancel selected booking' button for the vendor and admin tables; starts disabled."""
    return tk.Button(parent, text="Cancel selected booking", font=(t.FONT, 9, "bold"), bg="#e74c3c", fg="white",
                     disabledforeground="#f5c6c0", relief="flat", cursor="hand2", state=tk.DISABLED)
