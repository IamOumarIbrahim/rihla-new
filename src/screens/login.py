import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

import navigate
import theme as t
from brand_logo import draw_logo
from config import DEMO_ACCOUNTS, DEFAULT_LOGIN
from database import login, get_user_email
from screens.social_login import open_social_login
from ui import clear_window

# Left side (background picture with the logo)

_IMAGE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "background.jpg"))
_raw_bg_image = None
if os.path.exists(_IMAGE_PATH):
    try:
        _raw_bg_image = Image.open(_IMAGE_PATH)
        _raw_bg_image.load()
    except OSError:
        _raw_bg_image = None  # broken picture, just use the dark panel

_bg_photo = None

def _draw_scene(canvas, w, h):
    global _bg_photo
    canvas.delete("all")

    if w < 1 or h < 1:
        return

    if _raw_bg_image:
        img_w, img_h = _raw_bg_image.size

        # scale so it covers the whole canvas without stretching
        scale = w / img_w
        if h / img_h > scale:
            scale = h / img_h
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)

        resized_img = _raw_bg_image.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # cut the extra part off from the middle so it fits the panel
        left = (new_w - w) // 2
        top = (new_h - h) // 2
        cropped_img = resized_img.crop((left, top, left + w, top + h))

        _bg_photo = ImageTk.PhotoImage(cropped_img)
        canvas.create_image(0, 0, anchor=tk.NW, image=_bg_photo)
    else:
        canvas.config(bg=t.DARK)

    # logo instead of the title, if the logo file is missing just write the text
    if not draw_logo(canvas, w, h, h * 0.20 + 25):
        canvas.create_text(w / 2, h * 0.20, text="Rihla", fill="white", font=(t.FONT, 46, "bold"))


def _build_brand_panel(parent):
    canvas = tk.Canvas(parent, bg=t.DARK, highlightthickness=0)

    def on_resize(event):
        _draw_scene(canvas, event.width, event.height)
    canvas.bind("<Configure>", on_resize)
    return canvas


# Right side (the form)

def _make_field(parent, label_text, show=""):
    tk.Label(parent, text=label_text, font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(16, 5))

    field = tk.Frame(parent, bg=t.FIELD_BG, highlightthickness=1,
                     highlightbackground=t.BORDER, highlightcolor=t.PRIMARY)
    field.pack(fill=tk.X)

    entry = tk.Entry(field, font=(t.FONT, 11), bd=0, relief="flat", bg=t.FIELD_BG,
                     fg=t.TEXT, insertbackground=t.TEXT, show=show)
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, ipady=9)

    def focus_in(event):
        field.config(highlightbackground=t.PRIMARY)

    def focus_out(event):
        field.config(highlightbackground=t.BORDER)

    entry.bind("<FocusIn>", focus_in)
    entry.bind("<FocusOut>", focus_out)
    return field, entry


def show_login_screen(root, prefilled_email=None, prefilled_password=None):
    clear_window(root)

    if prefilled_email is None and prefilled_password is None:
        prefilled_email = DEFAULT_LOGIN[0]
        prefilled_password = DEFAULT_LOGIN[1]
    if not prefilled_email:
        prefilled_email = ""
    if not prefilled_password:
        prefilled_password = ""

    # brand panel on the left and the sign in card on the right
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
    tk.Frame(form, width=400, height=1, bg=t.CARD_BG).pack()  # keeps the form width fixed

    tk.Label(form, text="Welcome back", font=(t.FONT, 24, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w")
    tk.Label(form, text="Sign in to your Rihla account", font=(t.FONT, 11),
             bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(2, 0))

    # Fields
    email_field, email_entry = _make_field(form, "EMAIL")
    email_entry.insert(0, prefilled_email)

    password_field, password_entry = _make_field(form, "PASSWORD", show="*")
    password_entry.insert(0, prefilled_password)

    # show the password for 2 seconds
    def peek_password():
        password_entry.config(show="")

        def hide_again():
            password_entry.config(show="*")
        root.after(2000, hide_again)

    tk.Button(password_field, text="\U0001F441️", bd=0, relief="flat", bg=t.FIELD_BG,
              activebackground=t.FIELD_BG, cursor="hand2",
              command=peek_password).pack(side=tk.RIGHT, padx=8)

    def handle_login(event=None):
        email = email_entry.get().strip()
        password = password_entry.get()
        if not email or not password:
            messagebox.showerror("Error", "All fields are required.")
            return

        ok, message = login(email, password)
        if ok:
            saved_email = get_user_email(email)
            if not saved_email:
                saved_email = email
            navigate.show_welcome(root, saved_email)
        else:
            messagebox.showerror("Error", message)

    email_entry.bind("<Return>", handle_login)
    password_entry.bind("<Return>", handle_login)

    login_btn = tk.Button(form, text="Sign In", command=handle_login, font=(t.FONT, 11, "bold"),
                          bd=0, relief="flat", bg=t.PRIMARY, fg="white",
                          activebackground=t.PRIMARY_HOVER, activeforeground="white", cursor="hand2")
    login_btn.pack(fill=tk.X, pady=(22, 0), ipady=10)
    t.add_hover(login_btn, t.PRIMARY, t.PRIMARY_HOVER)

    # line with "or continue with" in the middle
    divider = tk.Frame(form, bg=t.CARD_BG)
    divider.pack(fill=tk.X, pady=20)
    tk.Frame(divider, bg=t.BORDER, height=1).pack(side=tk.LEFT, fill=tk.X, expand=True)
    tk.Label(divider, text="or continue with", font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT, padx=10)
    tk.Frame(divider, bg=t.BORDER, height=1).pack(side=tk.LEFT, fill=tk.X, expand=True)

    # Google and Apple buttons
    social = tk.Frame(form, bg=t.CARD_BG)
    social.pack(fill=tk.X)
    social.columnconfigure(0, weight=1, uniform="social")
    social.columnconfigure(1, weight=1, uniform="social")

    def open_google():
        open_social_login(root, "Google")

    def open_apple():
        open_social_login(root, "Apple")

    google_btn = tk.Button(social, text="Google", font=(t.FONT, 10, "bold"), bd=0, relief="flat",
                           bg="white", fg=t.TEXT, activebackground="#f4f6f7", cursor="hand2",
                           highlightthickness=1, highlightbackground=t.BORDER,
                           command=open_google)
    google_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6), ipady=7)
    t.add_hover(google_btn, "white", "#f4f6f7")

    apple_btn = tk.Button(social, text="Apple", font=(t.FONT, 10, "bold"), bd=0, relief="flat",
                          bg="white", fg=t.TEXT, activebackground="#f4f6f7", cursor="hand2",
                          highlightthickness=1, highlightbackground=t.BORDER,
                          command=open_apple)
    apple_btn.grid(row=0, column=1, sticky="ew", padx=(6, 0), ipady=7)
    t.add_hover(apple_btn, "white", "#f4f6f7")

    # Demo accounts
    tk.Label(form, text="QUICK DEMO ACCOUNTS", font=(t.FONT, 9, "bold"),
             bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(24, 6))

    def set_demo(role):
        email = DEMO_ACCOUNTS[role][0]
        password = DEMO_ACCOUNTS[role][1]
        email_entry.delete(0, tk.END)
        password_entry.delete(0, tk.END)
        email_entry.insert(0, email)
        password_entry.insert(0, password)

    chips = tk.Frame(form, bg=t.CARD_BG)
    chips.pack(fill=tk.X)
    per_row = 3  # 2 rows so all 6 roles fit
    i = 0
    for role in DEMO_ACCOUNTS:
        def pick_role(r=role):
            set_demo(r)
        chips.columnconfigure(i % per_row, weight=1, uniform="chip")
        chip = tk.Button(chips, text=role, font=(t.FONT, 9), bd=0, relief="flat",
                         bg=t.CHIP_BG, fg=t.TEXT, activebackground=t.CHIP_HOVER, cursor="hand2",
                         command=pick_role)
        chip.grid(row=i // per_row, column=i % per_row, sticky="ew", padx=2, pady=2, ipady=5)
        t.add_hover(chip, t.CHIP_BG, t.CHIP_HOVER)
        i += 1

    # links at the bottom
    def go_create_account():
        navigate.show_create_account(root)

    def go_forgot_password():
        navigate.show_forgot_password(root)

    links = tk.Frame(form, bg=t.CARD_BG)
    links.pack(fill=tk.X, pady=(26, 0))
    tk.Label(links, text="New to Rihla?", font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(side=tk.LEFT)
    tk.Button(links, text="Create an account", command=go_create_account, font=(t.FONT, 10, "bold"),
              bd=0, relief="flat", bg=t.CARD_BG, fg=t.PRIMARY,
              activebackground=t.CARD_BG, activeforeground=t.PRIMARY_HOVER,
              cursor="hand2").pack(side=tk.LEFT, padx=(4, 0))
    tk.Button(links, text="Forgot password?", command=go_forgot_password, font=(t.FONT, 10, "bold"),
              bd=0, relief="flat", bg=t.CARD_BG, fg=t.PRIMARY,
              activebackground=t.CARD_BG, activeforeground=t.PRIMARY_HOVER,
              cursor="hand2").pack(side=tk.RIGHT)

    email_entry.focus_set()
