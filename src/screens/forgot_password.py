import tkinter as tk
from tkinter import messagebox
from database import get_password_by_email
from ui import clear_window
import navigate
from .reset_password import show_reset_password_window

def show_forgot_password_screen(root):
    clear_window(root)

    tk.Label(root, text="Forgot Password", font=("Arial", 14, "bold")).pack(pady=20)

    tk.Label(root, text="Enter Registered Email").pack(pady=5)
    email_entry = tk.Entry(root, width=30)
    email_entry.pack(pady=5)

    status_label = tk.Label(root, text="", font=("Arial", 11, "bold"))
    status_label.pack(pady=5)

    code_frame = tk.Frame(root)

    tk.Label(code_frame, text="Enter 6-Digit Code").pack(pady=5)
    code_entry = tk.Entry(code_frame, width=30, show="*")
    code_entry.pack(pady=5)

    def verify_code():
        code = code_entry.get()
        if code == "000000":
            email = email_entry.get()
            status_label.config(text="Code verified! Opening reset window...", fg="green")
            root.after(1000, lambda: show_reset_password_window(root, email))
        else:
            messagebox.showerror("Error", "Invalid code. Please enter 000000.")

    tk.Button(code_frame, text="Verify Code", relief="raised", command=verify_code).pack(pady=10)

    def send_code():
        email = email_entry.get()
        if not email:
            messagebox.showerror("Error", "Email is required.")
            return

        stored_password = get_password_by_email(email)
        if not stored_password:
            messagebox.showerror("Error", "Email not found in database.")
            return

        status_label.config(text="Check your email for the 6-digit code.", fg="blue")
        code_frame.pack(pady=10)
        email_entry.config(state="disabled")
        submit_email_btn.config(state="disabled")

    submit_email_btn = tk.Button(root, text="Send Code", relief="raised", command=send_code)
    submit_email_btn.pack(pady=10)

    tk.Button(root, text="Back to Login", relief="raised",
              command=lambda: navigate.show_login(root)).pack(pady=5)