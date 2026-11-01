# things we need for cancelling bookings: the policy and refund text, the reason window and
# a page title with a Refresh button
#
# policy (the server checks it again): customers and partners get all the money back 48 hours or more
# before the event, half between 48 and 24 hours, and in the last 24 hours they cant cancel
# when a vendor or admin cancels its always a full refund with the VAT
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

import theme as t
from pricing import refund_breakdown

FULL_REFUND_HOURS = 48
HALF_REFUND_HOURS = 24
WHO = {"Vendor": "the vendor", "Admin": "Rihla support"}


def _when(text):
    if not text:
        text = ""
    try:
        return datetime.strptime(text[:16], "%Y-%m-%d %H:%M").strftime("%d %b %Y, %H:%M")
    except ValueError:
        return text


def refund_text(total, percent):
    base, vat, refund = refund_breakdown(total, percent)
    return (format(refund, ",.2f") + " AED (" + str(percent) + "%: " + format(base, ",.2f") + " + "
            + format(vat, ",.2f") + " VAT)")


# one line under a confirmed booking that says what you get back if you cancel now
def policy_line(booking):
    percent = booking.get("refund_if_cancelled")
    if percent == 100:
        return "Free cancellation until " + str(FULL_REFUND_HOURS) + " hours before the start."
    if percent == 50:
        return "Cancelling now refunds 50%. Cancellation closes " + str(HALF_REFUND_HOURS) + " hours before the start."
    return "Cancellation closed: it is less than " + str(HALF_REFUND_HOURS) + " hours before the start."


# like 'Cancelled 31 Oct 2026, 14:02 by the vendor: reason. Refunded 756.00 AED (100%: ...)'
def cancelled_line(booking, viewer_email=None):
    role = booking.get("cancelled_by_role")
    by = booking.get("cancelled_by")
    if not by:
        by = ""
    if viewer_email and by.lower() == viewer_email.lower():
        who = "you"
    elif role in WHO:
        who = WHO[role]
    elif by:
        who = by
    else:
        who = "the booker"
    text = "Cancelled"
    if booking.get("cancelled_at"):
        text += " " + _when(booking["cancelled_at"])
    text += " by " + who
    if booking.get("cancel_reason"):
        text += ": " + str(booking["cancel_reason"])
    if booking.get("refund_percent") is not None:
        text += ". Refunded " + refund_text(booking["total_price"], booking["refund_percent"]) + "."
    return text


# asks the booker if they are sure and shows the refund, True if they say yes
def confirm_own_cancel(booking):
    percent = booking.get("refund_if_cancelled")
    if percent is None:
        messagebox.showinfo("Cannot cancel", policy_line(booking))
        return False
    question = ("Cancel your booking for " + str(booking["event_title"]) + "?\n\n"
                + "Refund: " + refund_text(booking["total_price"], percent) + "\n"
                + "The ticket code will stop working.")
    return messagebox.askyesno("Cancel booking", question)


# window for the reason when a vendor or admin cancels somebody elses booking, gives back the reason or None
def ask_reason(parent, booking):
    win = tk.Toplevel(parent)
    win.title("Cancel booking")
    win.configure(bg=t.CARD_BG)
    win.resizable(False, False)
    win.transient(parent)
    win.grab_set()

    tk.Label(win, text="Cancel " + str(booking["customer_email"]) + "'s booking", font=(t.FONT, 13, "bold"),
             bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=20, pady=(16, 2))
    info = str(booking["event_title"]) + "  |  " + str(booking["booking_date"]) + "  |  " + str(booking["guests"]) + " guest(s)"
    tk.Label(win, text=info,
             font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=20)
    tk.Label(win, text="Full refund: " + refund_text(booking["total_price"], 100), font=(t.FONT, 10, "bold"),
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

    def on_escape(event):
        win.destroy()

    btns = tk.Frame(win, bg=t.CARD_BG)
    btns.pack(fill=tk.X, padx=20, pady=(0, 16))
    tk.Button(btns, text="Cancel booking and refund", font=(t.FONT, 10, "bold"), bg="#e74c3c", fg="white",
              relief="flat", cursor="hand2", command=confirm).pack(side=tk.LEFT, ipadx=10, ipady=5)
    tk.Button(btns, text="Keep booking", font=(t.FONT, 10), bg=t.CHIP_BG, fg=t.TEXT, relief="flat",
              cursor="hand2", command=win.destroy).pack(side=tk.LEFT, padx=8, ipadx=10, ipady=5)
    win.bind("<Escape>", on_escape)
    parent.wait_window(win)
    return result["reason"]


# page title with Refresh on the right, for the pages that show changes from other people
def page_header(parent, title, on_refresh, pady=(20, 5)):
    row = tk.Frame(parent, bg=t.PAGE_BG)
    row.pack(fill=tk.X, padx=30, pady=pady)
    tk.Label(row, text=title, font=(t.FONT, 22, "bold"), bg=t.PAGE_BG, fg=t.TEXT).pack(side=tk.LEFT)
    btn = tk.Button(row, text="Refresh", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT, relief="solid", bd=1,
                    cursor="hand2", command=on_refresh)
    btn.pack(side=tk.RIGHT, ipadx=10, ipady=3)
    t.add_hover(btn, t.CARD_BG, t.CHIP_HOVER)
    return row


# red 'Cancel selected booking' button for the vendor and admin tables, its disabled at the start
def cancel_button(parent):
    return tk.Button(parent, text="Cancel selected booking", font=(t.FONT, 9, "bold"), bg="#e74c3c", fg="white",
                     disabledforeground="#f5c6c0", relief="flat", cursor="hand2", state=tk.DISABLED)
