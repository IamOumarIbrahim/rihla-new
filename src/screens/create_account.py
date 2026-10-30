import math
import random
import re
import tkinter as tk
from tkinter import messagebox

import navigate
import theme as t
from config import ROLES, MIN_PASSWORD_LENGTH
from database import register_user, email_exists, phone_exists
from ui import clear_window

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _valid_phone(value):
    """UAE mobile number without the +971 prefix: exactly 9 digits (spaces allowed)."""
    digits = re.sub(r"\s+", "", value)
    return digits.isascii() and digits.isdigit() and len(digits) == 9

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
    canvas.create_text(w / 2, h * 0.20 + 62, text="Start your journey with us.", fill="#bdc3c7", font=(t.FONT, 14))


def _build_brand_panel(parent):
    canvas = tk.Canvas(parent, bg=t.DARK, highlightthickness=0)
    canvas.bind("<Configure>", lambda e: _draw_scene(canvas, e.width, e.height))
    return canvas


def _make_field(parent, label_text, show=""):
    tk.Label(parent, text=label_text, font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(10, 3))
    field = tk.Frame(parent, bg=t.FIELD_BG, highlightthickness=1, highlightbackground=t.BORDER, highlightcolor=t.PRIMARY)
    field.pack(fill=tk.X)
    entry = tk.Entry(field, font=(t.FONT, 11), bd=0, relief="flat", bg=t.FIELD_BG, fg=t.TEXT, insertbackground=t.TEXT, show=show)
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, ipady=7)
    entry.bind("<FocusIn>", lambda e: field.config(highlightbackground=t.PRIMARY))
    entry.bind("<FocusOut>", lambda e: field.config(highlightbackground=t.BORDER))
    return field, entry


def show_create_account_screen(root):
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
    tk.Frame(form, width=420, height=1, bg=t.CARD_BG).pack()

    tk.Label(form, text="Create Account", font=(t.FONT, 22, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w")
    tk.Label(form, text="Fill in your details to get started", font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(2, 10))

    _, reg_email = _make_field(form, "EMAIL")
    verification_status = {"email": False, "phone": False, "email_value": None, "phone_value": None}

    email_status = tk.Label(form, text="Email: Not Verified", font=(t.FONT, 9), bg=t.CARD_BG, fg="#e74c3c")
    email_status.pack(anchor="w", pady=2)

    def verify_email():
        email_val = reg_email.get().strip()
        if not email_val:
            messagebox.showerror("Error", "Please enter an email first.")
            return
        if not _EMAIL_RE.match(email_val):
            messagebox.showerror("Error", "Please enter a valid email address.")
            return
        if email_exists(email_val):
            messagebox.showerror("Error", "Email already exists. Please log in.")
            return
        
        win = tk.Toplevel(root)
        win.title("Verify Email")
        win.geometry("280x150")
        tk.Label(win, text="Enter code: 000000", font=(t.FONT, 10)).pack(pady=10)
        code_e = tk.Entry(win, width=20, show="*")
        code_e.pack(pady=5)
        def check():
            if code_e.get() == "000000":
                verification_status["email"] = True
                verification_status["email_value"] = email_val.lower()
                email_status.config(text="Email: Verified ✓", fg="#27ae60")
                win.destroy()
            else:
                messagebox.showerror("Error", "Invalid code. Use 000000.", parent=win)
        tk.Button(win, text="Confirm", command=check).pack(pady=10)

    tk.Button(form, text="Verify Email", font=(t.FONT, 9, "bold"), bg=t.PRIMARY, fg="white", bd=0, relief="flat", command=verify_email).pack(anchor="w", pady=2, ipady=4, ipadx=10)

    tk.Label(form, text="PHONE NUMBER", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(8, 3))
    phone_box = tk.Frame(form, bg=t.FIELD_BG, highlightthickness=1, highlightbackground=t.BORDER)
    phone_box.pack(fill=tk.X)
    tk.Label(phone_box, text="+971", font=(t.FONT, 10, "bold"), bg=t.FIELD_BG, fg=t.TEXT).pack(side=tk.LEFT, padx=8)
    reg_phone = tk.Entry(phone_box, font=(t.FONT, 11), bd=0, relief="flat", bg=t.FIELD_BG, fg=t.TEXT, insertbackground=t.TEXT)
    reg_phone.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, ipady=7)
    reg_phone.insert(0, "50 1234567")

    phone_status = tk.Label(form, text="Phone: Not Verified", font=(t.FONT, 9), bg=t.CARD_BG, fg="#e74c3c")
    phone_status.pack(anchor="w", pady=2)

    def verify_phone():
        if not _valid_phone(reg_phone.get()):
            messagebox.showerror("Error", "Enter a valid UAE mobile number (9 digits after +971).")
            return
        p_val = "+971 " + reg_phone.get().strip()
        if phone_exists(p_val):
            messagebox.showerror("Error", "Phone number already in use.")
            return
        win = tk.Toplevel(root)
        win.title("Verify Phone")
        win.geometry("280x150")
        tk.Label(win, text="Enter code: 000000", font=(t.FONT, 10)).pack(pady=10)
        code_e = tk.Entry(win, width=20, show="*")
        code_e.pack(pady=5)
        def check():
            if code_e.get() == "000000":
                verification_status["phone"] = True
                verification_status["phone_value"] = p_val
                phone_status.config(text="Phone: Verified ✓", fg="#27ae60")
                win.destroy()
            else:
                messagebox.showerror("Error", "Invalid code. Use 000000.", parent=win)
        tk.Button(win, text="Confirm", command=check).pack(pady=10)

    tk.Button(form, text="Verify Phone", font=(t.FONT, 9, "bold"), bg=t.PRIMARY, fg="white", bd=0, relief="flat", command=verify_phone).pack(anchor="w", pady=2, ipady=4, ipadx=10)

    password_field, reg_pass = _make_field(form, "PASSWORD", show="*")
    
    # View password for 2 seconds function
    def peek_password(entry_widget):
        entry_widget.config(show="")
        root.after(2000, lambda: entry_widget.config(show="*"))

    tk.Button(password_field, text="\U0001F441\uFE0F", bd=0, relief="flat", bg=t.FIELD_BG,
              activebackground=t.FIELD_BG, cursor="hand2",
              command=lambda: peek_password(reg_pass)).pack(side=tk.RIGHT, padx=8)

    strength_label = tk.Label(form, text="Strength: Too weak", font=(t.FONT, 9), bg=t.CARD_BG, fg="#e74c3c")
    strength_label.pack(anchor="w", pady=2)

    def update_strength(event=None):
        pwd = reg_pass.get()
        if not pwd:
            strength_label.config(text="Strength: Too weak", fg="#e74c3c")
            return
        score = 0
        if len(pwd) >= 8: score += 1
        if any(c.isupper() for c in pwd): score += 1
        if any(c.isdigit() for c in pwd): score += 1
        if any(c in "!@#$%^&*()" for c in pwd): score += 1

        if score <= 1:
            strength_label.config(text="Strength: Weak", fg="#e74c3c")
        elif score == 2 or score == 3:
            strength_label.config(text="Strength: Medium", fg="#f39c12")
        else:
            strength_label.config(text="Strength: Strong", fg="#27ae60")

    reg_pass.bind("<KeyRelease>", update_strength)

    confirm_field, reg_confirm = _make_field(form, "CONFIRM PASSWORD", show="*")

    tk.Button(confirm_field, text="\U0001F441\uFE0F", bd=0, relief="flat", bg=t.FIELD_BG,
              activebackground=t.FIELD_BG, cursor="hand2",
              command=lambda: peek_password(reg_confirm)).pack(side=tk.RIGHT, padx=8)

    terms_var = tk.BooleanVar(value=False)
    terms_check = tk.Checkbutton(form, text="I agree to the Terms & Conditions", variable=terms_var, font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT, activebackground=t.CARD_BG)
    terms_check.pack(anchor="w", pady=(8, 4))

    def handle_register():
        email = reg_email.get().strip()
        pwd = reg_pass.get()
        confirm = reg_confirm.get()
        phone = "+971 " + reg_phone.get().strip()

        if not pwd or pwd.strip().lower() in ["null", "none", "password", "123456"] or len(pwd) < MIN_PASSWORD_LENGTH:
            messagebox.showerror("Error", f"Please choose a valid, secure password (at least {MIN_PASSWORD_LENGTH} characters).")
            return

        if pwd != confirm:
            messagebox.showerror("Error", "Passwords do not match.")
            return

        if not verification_status["email"] or not verification_status["phone"]:
            messagebox.showerror("Error", "You must verify both email and phone.")
            return

        # The person must not change the email or phone after the verification step.
        if email.lower() != verification_status["email_value"]:
            verification_status["email"] = False
            email_status.config(text="Email: Not Verified", fg="#e74c3c")
        if phone != verification_status["phone_value"]:
            verification_status["phone"] = False
            phone_status.config(text="Phone: Not Verified", fg="#e74c3c")
        if not verification_status["email"] or not verification_status["phone"]:
            messagebox.showerror("Error", "Email or phone changed after verification. Please verify them again.")
            return

        if not terms_var.get():
            messagebox.showerror("Error", "You must agree to the Terms & Conditions.")
            return

        if register_user(email, pwd, "Customer", phone=phone):
            navigate.show_welcome(root, email)
        else:
            messagebox.showerror("Error", "Registration failed. An account with this email already exists.")

    reg_btn = tk.Button(form, text="Create Account", font=(t.FONT, 11, "bold"), bg=t.PRIMARY, fg="white", bd=0, relief="flat", command=handle_register)
    reg_btn.pack(fill=tk.X, pady=(15, 0), ipady=8)

    back_btn = tk.Button(form, text="Back to Login", font=(t.FONT, 9), bg=t.CARD_BG, fg=t.PRIMARY, bd=0, relief="flat", command=lambda: navigate.show_login(root))
    back_btn.pack(pady=(10, 0))