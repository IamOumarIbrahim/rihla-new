import tkinter as tk
from tkinter import messagebox

from database import login, get_user_email
import navigate


def open_social_login(root, provider):
    social_window = tk.Toplevel(root)
    social_window.title("Sign in with " + provider)
    social_window.geometry("350x300")

    tk.Label(social_window, text="Sign in with " + provider, font=("Arial", 14, "bold")).pack(pady=15)
    tk.Label(social_window, text="Email").pack(pady=2)
    email_entry = tk.Entry(social_window, width=25)
    email_entry.pack(pady=5)

    tk.Label(social_window, text="Password").pack(pady=2)
    password_entry = tk.Entry(social_window, width=25, show="*")
    password_entry.pack(pady=5)

    def handle_social_login():
        email = email_entry.get().strip()
        password = password_entry.get()
        if not email or not password:
            messagebox.showerror("Error", "All fields are required.", parent=social_window)
            return

        ok, message = login(email, password)
        if ok:
            social_window.destroy()
            saved_email = get_user_email(email)
            if not saved_email:
                saved_email = email
            navigate.show_welcome(root, saved_email)
        else:
            messagebox.showerror("Error", message, parent=social_window)

    tk.Button(social_window, text="Continue with " + provider, command=handle_social_login).pack(pady=20)
