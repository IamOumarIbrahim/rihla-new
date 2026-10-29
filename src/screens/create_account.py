import tkinter as tk
from tkinter import messagebox

from config import ROLES
from database import register_user
from ui import clear_window
import navigate


def show_create_account_screen(root):
    clear_window(root)

    tk.Label(root, text="Create New Account", font=("Arial", 14, "bold")).pack(pady=20)

    tk.Label(root, text="Email").pack(pady=5)
    reg_email = tk.Entry(root, width=30)
    reg_email.pack(pady=5)

    tk.Label(root, text="Password").pack(pady=5)
    reg_pass = tk.Entry(root, width=30, show="*")
    reg_pass.pack(pady=5)

    tk.Label(root, text="Confirm Password").pack(pady=5)
    reg_confirm = tk.Entry(root, width=30, show="*")
    reg_confirm.pack(pady=5)

    # Account type selection
    tk.Label(root, text="Account Type", font=("Arial", 11, "bold")).pack(pady=(15, 5))
    account_type = tk.StringVar(value="Customer")
    type_frame = tk.Frame(root)
    type_frame.pack(pady=5)
    for role in ROLES:
        tk.Radiobutton(type_frame, text=role, variable=account_type, value=role).pack(anchor="w")

    def register():
        email = reg_email.get()
        password = reg_pass.get()
        confirm = reg_confirm.get()
        role = account_type.get()

        if not email or not password or not confirm:
            messagebox.showerror("Error", "All fields are required.")
            return

        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match.")
            return

        if not role:
            messagebox.showerror("Error", "Please select an account type.")
            return

        if register_user(email, password, role):
            navigate.show_welcome(root, email)
        else:
            messagebox.showerror("Error", "Email already exists in the database.")

    tk.Button(root, text="Register", relief="raised", command=register).pack(pady=20)
    tk.Button(root, text="Back to Login", relief="raised",
              command=lambda: navigate.show_login(root)).pack(pady=5)