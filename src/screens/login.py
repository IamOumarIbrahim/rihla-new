import math
import random
import tkinter as tk
from tkinter import messagebox

import navigate
import theme as t
from config import DEMO_ACCOUNTS, DEFAULT_LOGIN
from database import check_login
from screens.social_login import open_social_login
from ui import clear_window

_rng = random.Random(7)
_STARS = [(_rng.random(), _rng.random() * 0.5) for _ in range(45)]


# ---------- left side: branding scene ----------
def _draw_dune(canvas, w, h, base, amp, freq, phase, color):
    points = []
    for x in range(-10, w + 20, 10):
        y = h * base + h * amp * math.sin(x / max(w, 1) * freq * math.pi + phase)
        points.extend((x, y))
    points.extend((w + 20, h + 10, -10, h + 10))
    canvas.create_polygon(points, fill=color, outline="")


def _draw_scene(canvas, w, h):
    canvas.delete("all")

    # stars
    for rx, ry in _STARS:
        x, y = rx * w, ry * h
        canvas.create_oval(x - 1.5, y - 1.5, x + 1.5, y + 1.5, fill="#aab7c4", outline="")

    # sun with soft glow
    cx, cy, r = w * 0.5, h * 0.66, min(w, h) * 0.12
    canvas.create_oval(cx - r * 1.7, cy - r * 1.7, cx + r * 1.7, cy + r * 1.7, fill="#34495e", outline="")
    canvas.create_oval(cx - r * 1.35, cy - r * 1.35, cx + r * 1.35, cy + r * 1.35, fill="#4a6580", outline="")
    canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#f5b041", outline="")

    # dunes (back to front)
    _draw_dune(canvas, w, h, 0.74, 0.040, 2.2, 0.5, "#e67e22")
    _draw_dune(canvas, w, h, 0.82, 0.035, 3.0, 2.0, "#d35400")
    _draw_dune(canvas, w, h, 0.90, 0.030, 2.0, 4.0, "#a04000")

    # title + tagline
    canvas.create_text(w / 2, h * 0.20, text="Rihla", fill="white", font=(t.FONT, 46, "bold"))
    canvas.create_text(w / 2, h * 0.20 + 62, text="Discover the desert, your way.", fill="#bdc3c7", font=(t.FONT, 14))


def _build_brand_panel(parent):
    canvas = tk.Canvas(parent, bg=t.DARK, highlightthickness=0)
    canvas.bind("<Configure>", lambda e: _draw_scene(canvas, e.width, e.height))
    return canvas


# ---------- right side: form pieces ----------
def _make_field(parent, label_text, show=""):
    tk.Label(parent, text=label_text, font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(16, 5))

    field = tk.Frame(parent, bg=t.FIELD_BG, highlightthickness=1,
                     highlightbackground=t.BORDER, highlightcolor=t.PRIMARY)
    field.pack(fill=tk.X)

    entry = tk.Entry(field, font=(t.FONT, 11), bd=0, relief="flat", bg=t.FIELD_BG,
                     fg=t.TEXT, insertbackground=t.TEXT, show=show)
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, ipady=9)

    entry.bind("<FocusIn>", lambda e: field.config(highlightbackground=t.PRIMARY))
    entry.bind("<FocusOut>", lambda e: field.config(highlightbackground=t.BORDER))
    return field, entry


def _link_button(parent, text, command):
    return tk.Button(parent, text=text, command=command, font=(t.FONT, 10, "bold"),
                     bd=0, relief="flat", bg=t.CARD_BG, fg=t.PRIMARY,
                     activebackground=t.CARD_BG, activeforeground=t.PRIMARY_HOVER,
                     cursor="hand2")


def show_login_screen(root, prefilled_email=None, prefilled_password=None):
    clear_window(root)

    if prefilled_email is None and prefilled_password is None:
        prefilled_email, prefilled_password = DEFAULT_LOGIN
    prefilled_email = prefilled_email or ""
    prefilled_password = prefilled_password or ""

    # ----- page layout: brand panel left, sign-in card right -----
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
    tk.Frame(form, width=400, height=1, bg=t.CARD_BG).pack()  # fixes the form width

    # ----- heading -----
    tk.Label(form, text="Welcome back", font=(t.FONT, 24, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w")
    tk.Label(form, text="Sign in to your Rihla account", font=(t.FONT, 11),
             bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(2, 0))

    # ----- fields -----
    _, email_entry = _make_field(form, "EMAIL")
    email_entry.insert(0, prefilled_email)

    password_field, password_entry = _make_field(form, "PASSWORD", show="*")
    password_entry.insert(0, prefilled_password)

    # View password for 2 seconds
    def peek_password():
        password_entry.config(show="")
        root.after(2000, lambda: password_entry.config(show="*"))

    tk.Button(password_field, text="\U0001F441\uFE0F", bd=0, relief="flat", bg=t.FIELD_BG,
              activebackground=t.FIELD_BG, cursor="hand2",
              command=lambda: peek_password()).pack(side=tk.RIGHT, padx=8)

    def handle_login(event=None):
        email = email_entry.get()
        password = password_entry.get()
        if not email or not password:
            messagebox.showerror("Error", "All fields are required.")
            return

        if check_login(email, password):
            navigate.show_welcome(root, email)
        else:
            messagebox.showerror("Error", "Invalid email or password.")

    email_entry.bind("<Return>", handle_login)
    password_entry.bind("<Return>", handle_login)

    # ----- primary action -----
    login_btn = tk.Button(form, text="Sign In", command=handle_login, font=(t.FONT, 11, "bold"),
                          bd=0, relief="flat", bg=t.PRIMARY, fg="white",
                          activebackground=t.PRIMARY_HOVER, activeforeground="white", cursor="hand2")
    login_btn.pack(fill=tk.X, pady=(22, 0), ipady=10)
    t.add_hover(login_btn, t.PRIMARY, t.PRIMARY_HOVER)

    # ----- divider -----
    divider = tk.Frame(form, bg=t.CARD_BG)
    divider.pack(fill=tk.X, pady=20)
    tk.Frame(divider, bg=t.BORDER, height=1).pack(side=tk.LEFT, fill=tk.X, expand=True)
    tk.Label(divider, text="or continue with", font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT, padx=10)
    tk.Frame(divider, bg=t.BORDER, height=1).pack(side=tk.LEFT, fill=tk.X, expand=True)

    # ----- social buttons -----
    social = tk.Frame(form, bg=t.CARD_BG)
    social.pack(fill=tk.X)
    social.columnconfigure(0, weight=1, uniform="social")
    social.columnconfigure(1, weight=1, uniform="social")
    for col, provider in enumerate(("Google", "Apple")):
        btn = tk.Button(social, text=provider, font=(t.FONT, 10, "bold"), bd=0, relief="flat",
                        bg="white", fg=t.TEXT, activebackground="#f4f6f7", cursor="hand2",
                        highlightthickness=1, highlightbackground=t.BORDER,
                        command=lambda p=provider: open_social_login(root, p))
        btn.grid(row=0, column=col, sticky="ew", padx=(0, 6) if col == 0 else (6, 0), ipady=7)
        t.add_hover(btn, "white", "#f4f6f7")

    # ----- demo accounts -----
    tk.Label(form, text="QUICK DEMO ACCOUNTS", font=(t.FONT, 9, "bold"),
             bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(24, 6))

    def set_demo(role):
        email, password = DEMO_ACCOUNTS[role]
        email_entry.delete(0, tk.END)
        password_entry.delete(0, tk.END)
        email_entry.insert(0, email)
        password_entry.insert(0, password)

    chips = tk.Frame(form, bg=t.CARD_BG)
    chips.pack(fill=tk.X)
    for i, role in enumerate(DEMO_ACCOUNTS):
        chips.columnconfigure(i, weight=1, uniform="chip")
        chip = tk.Button(chips, text=role, font=(t.FONT, 9), bd=0, relief="flat",
                         bg=t.CHIP_BG, fg=t.TEXT, activebackground=t.CHIP_HOVER, cursor="hand2",
                         command=lambda r=role: set_demo(r))
        chip.grid(row=0, column=i, sticky="ew", padx=2, ipady=5)
        t.add_hover(chip, t.CHIP_BG, t.CHIP_HOVER)

    # ----- bottom links -----
    links = tk.Frame(form, bg=t.CARD_BG)
    links.pack(fill=tk.X, pady=(26, 0))
    tk.Label(links, text="New to Rihla?", font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT)
    _link_button(links, "Create an account", lambda: navigate.show_create_account(root)).pack(side=tk.LEFT, padx=(4, 0))
    _link_button(links, "Forgot password?", lambda: navigate.show_forgot_password(root)).pack(side=tk.RIGHT)

    email_entry.focus_set()