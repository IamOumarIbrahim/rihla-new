import math
import random
import tkinter as tk
from tkinter import messagebox

import navigate
import theme as t
from database import get_password_by_email
from ui import clear_window
from .reset_password import show_reset_password_window

_rng = random.Random(7)
_STARS = [(_rng.random(), _rng.random() * 0.5) for _ in range(45)]


def _draw_dune(canvas, w, h, base, amp, freq, phase, color):
    points = []
    for x in range(-10, w + 20, 10):
        y = h * base + h * amp * math.sin(x / max(w, 1) * freq * math.pi + phase)
        points.extend((x, y))
    points.extend((w + 20, h + 10, -10, h + 10))
    canvas.create_polygon(points, fill=color, outline="")


def _draw_scene(canvas, w, h):
    canvas.delete("all")
    for rx, ry in _STARS:
        x, y = rx * w, ry * h
        canvas.create_oval(x - 1.5, y - 1.5, x + 1.5, y + 1.5, fill="#aab7c4", outline="")

    cx, cy, r = w * 0.5, h * 0.66, min(w, h) * 0.12
    canvas.create_oval(cx - r * 1.7, cy - r * 1.7, cx + r * 1.7, cy + r * 1.7, fill="#34495e", outline="")
    canvas.create_oval(cx - r * 1.35, cy - r * 1.35, cx + r * 1.35, cy + r * 1.35, fill="#4a6580", outline="")
    canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#f5b041", outline="")

    _draw_dune(canvas, w, h, 0.74, 0.040, 2.2, 0.5, "#e67e22")
    _draw_dune(canvas, w, h, 0.82, 0.035, 3.0, 2.0, "#d35400")
    _draw_dune(canvas, w, h, 0.90, 0.030, 2.0, 4.0, "#a04000")

    canvas.create_text(w / 2, h * 0.20, text="Rihla", fill="white", font=(t.FONT, 46, "bold"))
    canvas.create_text(w / 2, h * 0.20 + 62, text="Password recovery made easy.", fill="#bdc3c7", font=(t.FONT, 14))


def _build_brand_panel(parent):
    canvas = tk.Canvas(parent, bg=t.DARK, highlightthickness=0)
    canvas.bind("<Configure>", lambda e: _draw_scene(canvas, e.width, e.height))
    return canvas


def _make_field(parent, label_text, show=""):
    tk.Label(parent, text=label_text, font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(12, 4))
    field = tk.Frame(parent, bg=t.FIELD_BG, highlightthickness=1, highlightbackground=t.BORDER, highlightcolor=t.PRIMARY)
    field.pack(fill=tk.X)
    entry = tk.Entry(field, font=(t.FONT, 11), bd=0, relief="flat", bg=t.FIELD_BG, fg=t.TEXT, insertbackground=t.TEXT, show=show)
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, ipady=8)
    entry.bind("<FocusIn>", lambda e: field.config(highlightbackground=t.PRIMARY))
    entry.bind("<FocusOut>", lambda e: field.config(highlightbackground=t.BORDER))
    return field, entry


def show_forgot_password_screen(root):
    clear_window(root)

    container = tk.Frame(root, bg=t.CARD_BG)
    container.pack(fill=tk.BOTH, expand=True)
    container.rowconfigure(0, weight=1)
    container.columnconfigure(0, weight=5, uniform="cols")
    container.columnconfigure(1, weight=4, uniform="cols")

    _build_brand_panel(container).grid(row=0, column=0, sticky="nsew")

    right = tk.Frame(container, bg=t.CARD_BG)
    right.grid(row=0, column=1, sticky="nsew")

    form = tk.Frame(right, bg=t.CARD_BG)
    form.place(relx=0.5, rely=0.5, anchor="center")
    tk.Frame(form, width=400, height=1, bg=t.CARD_BG).pack()

    tk.Label(form, text="Forgot Password", font=(t.FONT, 24, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w")
    tk.Label(form, text="Enter your email to receive a verification code", font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(2, 15))

    _, email_entry = _make_field(form, "REGISTERED EMAIL")

    status_label = tk.Label(form, text="", font=(t.FONT, 9, "bold"), bg=t.CARD_BG)
    status_label.pack(anchor="w", pady=(8, 0))

    code_container = tk.Frame(form, bg=t.CARD_BG)
    _, code_entry = _make_field(code_container, "ENTER 6-DIGIT CODE (HINT: 000000)", show="*")

    def verify_code():
        code = code_entry.get().strip()
        if code == "000000":
            email = email_entry.get().strip()
            status_label.config(text="Code verified! Opening reset window...", fg="#27ae60")
            root.after(1000, lambda: show_reset_password_window(root, email))
        else:
            messagebox.showerror("Error", "Invalid code. Please enter 000000.")

    verify_btn = tk.Button(code_container, text="Verify Code", font=(t.FONT, 11, "bold"), bd=0, relief="flat",
                           bg=t.PRIMARY, fg="white", activebackground=t.PRIMARY_HOVER, cursor="hand2",
                           command=verify_code)
    verify_btn.pack(fill=tk.X, pady=(15, 0), ipady=9)
    t.add_hover(verify_btn, t.PRIMARY, t.PRIMARY_HOVER)

    def send_code():
        email = email_entry.get().strip()
        if not email:
            messagebox.showerror("Error", "Email is required.")
            return

        stored_password = get_password_by_email(email)
        if not stored_password:
            messagebox.showerror("Error", "Email not found in database.")
            return

        status_label.config(text="Check your email for the 6-digit code.", fg="#3498db")
        code_container.pack(fill=tk.X, pady=(10, 0))
        email_entry.config(state="disabled")
        send_btn.config(state="disabled", bg=t.BORDER)

    send_btn = tk.Button(form, text="Send Code", font=(t.FONT, 11, "bold"), bd=0, relief="flat",
                         bg=t.PRIMARY, fg="white", activebackground=t.PRIMARY_HOVER, cursor="hand2",
                         command=send_code)
    send_btn.pack(fill=tk.X, pady=(15, 0), ipady=9)
    t.add_hover(send_btn, t.PRIMARY, t.PRIMARY_HOVER)

    back_btn = tk.Button(form, text="Back to Login", font=(t.FONT, 10, "bold"), bd=0, relief="flat",
                         bg=t.CARD_BG, fg=t.PRIMARY, activebackground=t.CARD_BG, cursor="hand2",
                         command=lambda: navigate.show_login(root))
    back_btn.pack(anchor="w", pady=(20, 0))

    email_entry.focus_set()