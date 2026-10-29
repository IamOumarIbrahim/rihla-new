import tkinter as tk
from tkinter import messagebox
from database import update_password
import navigate

def show_reset_password_window(root, email):
    reset_win = tk.Toplevel(root)
    reset_win.title("Reset Password")
    reset_win.geometry("350x300")

    tk.Label(reset_win, text="Reset Password", font=("Arial", 14, "bold")).pack(pady=15)

    tk.Label(reset_win, text="New Password").pack(pady=2)
    new_pass_entry = tk.Entry(reset_win, width=25, show="*")
    new_pass_entry.pack(pady=5)

    tk.Label(reset_win, text="Confirm New Password").pack(pady=2)
    confirm_pass_entry = tk.Entry(reset_win, width=25, show="*")
    confirm_pass_entry.pack(pady=5)

    def handle_reset():
        new_pass = new_pass_entry.get()
        confirm_pass = confirm_pass_entry.get()

        if not new_pass or not confirm_pass:
            messagebox.showerror("Error", "All fields are required.", parent=reset_win)
            return

        if new_pass != confirm_pass:
            messagebox.showerror("Error", "Passwords do not match.", parent=reset_win)
            return

        update_password(email, new_pass)
        messagebox.showinfo("Success", "Password updated successfully!", parent=reset_win)
        reset_win.destroy()
        navigate.show_login(root, prefilled_email=email, prefilled_password=new_pass)

    tk.Button(reset_win, text="Update Password", command=handle_reset).pack(pady=20)