import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

import navigate
import theme as t
from brand_logo import draw_logo
from database import email_exists
from ui import clear_window
from .reset_password import show_reset_password_window

_IMAGE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "background.jpg"))
_raw_bg_image = None
if os.path.exists(_IMAGE_PATH):
    try:
        _raw_bg_image = Image.open(_IMAGE_PATH)
        _raw_bg_image.load()
    except OSError:
        _raw_bg_image = None  # Broken image file: fall back to the plain dark panel

_bg_photo = None


def _draw_scene(canvas, w, h):
    global _bg_photo
    canvas.delete("all")

    if w < 1 or h < 1:
        return

    if _raw_bg_image:
        img_w, img_h = _raw_bg_image.size

        # Scale to cover the canvas without stretching, then crop the overflow from the center
        scale = max(w / img_w, h / img_h)
        new_w = max(int(img_w * scale), w)
        new_h = max(int(img_h * scale), h)
        resized_img = _raw_bg_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left = (new_w - w) // 2
        top = (new_h - h) // 2
        _bg_photo = ImageTk.PhotoImage(resized_img.crop((left, top, left + w, top + h)))
        canvas.create_image(0, 0, anchor=tk.NW, image=_bg_photo)
    else:
        canvas.config(bg=t.DARK)

    # Logo in place of the title text; fall back to plain text if the image is missing
    if not draw_logo(canvas, w, h, h * 0.20 + 25):
        canvas.create_text(w / 2, h * 0.20, text="Rihla", fill="white", font=(t.FONT, 46, "bold"))


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

        if not email_exists(email):
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