import os
import re
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

import navigate
import theme as t
from brand_logo import draw_logo
from config import SIGNUP_ROLES, MIN_PASSWORD_LENGTH
from database import register_user, email_exists, phone_exists
from digit_boxes import DigitBoxes

SSN_LENGTH = 16
from ui import clear_window

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _valid_phone(value):
    """UAE mobile number without the +971 prefix: exactly 9 digits (spaces allowed)."""
    digits = re.sub(r"\s+", "", value)
    return digits.isascii() and digits.isdigit() and len(digits) == 9

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

    # Account type: customers sign up as before; every other role must also give a 16-digit SSN.
    role_row = tk.Frame(form, bg=t.CARD_BG)
    role_row.pack(fill=tk.X, pady=(2, 0))
    tk.Label(role_row, text="ACCOUNT TYPE", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT)
    role_var = tk.StringVar(value="Customer")
    role_menu = tk.OptionMenu(role_row, role_var, *SIGNUP_ROLES)
    role_menu.config(font=(t.FONT, 10), bg=t.FIELD_BG, fg=t.TEXT, activebackground=t.FIELD_BG, relief="flat", bd=0,
                     highlightthickness=1, highlightbackground=t.BORDER, anchor="w", cursor="hand2", width=14)
    role_menu["menu"].config(font=(t.FONT, 10))
    role_menu.pack(side=tk.RIGHT)

    ssn_section = tk.Frame(form, bg=t.CARD_BG)
    tk.Label(ssn_section, text=f"SSN ({SSN_LENGTH} DIGITS)", font=(t.FONT, 9, "bold"),
             bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(8, 3))
    ssn_boxes = DigitBoxes(ssn_section, groups=4, group_size=4, font_size=12, box_width=1)
    ssn_boxes.pack(anchor="w")

    def on_role_change(*_):
        if role_var.get() == "Customer":
            ssn_boxes.set("")
            ssn_section.pack_forget()
        else:
            ssn_section.pack(fill=tk.X, after=role_row)

    role_var.trace_add("write", on_role_change)

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
                email_status.config(text="Email: Verified", fg="#27ae60")
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
                phone_status.config(text="Phone: Verified", fg="#27ae60")
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

        role = role_var.get()
        ssn = None
        if role != "Customer":
            ssn = ssn_boxes.get()
            if not ssn_boxes.is_complete():
                ssn_boxes.set_error(True)
                messagebox.showerror("Error", f"{role} accounts must enter all {SSN_LENGTH} digits of their SSN.")
                return
            if len(set(ssn)) == 1:
                ssn_boxes.set_error(True)
                messagebox.showerror("Error", "Please enter your real SSN.")
                return

        if register_user(email, pwd, role, phone=phone, ssn=ssn):
            navigate.show_welcome(root, email)
        else:
            messagebox.showerror("Error", "Registration failed. An account with this email already exists.")

    reg_btn = tk.Button(form, text="Create Account", font=(t.FONT, 11, "bold"), bg=t.PRIMARY, fg="white", bd=0, relief="flat", command=handle_register)
    reg_btn.pack(fill=tk.X, pady=(15, 0), ipady=8)

    back_btn = tk.Button(form, text="Back to Login", font=(t.FONT, 9), bg=t.CARD_BG, fg=t.PRIMARY, bd=0, relief="flat", command=lambda: navigate.show_login(root))
    back_btn.pack(pady=(10, 0))