import tkinter as tk
from tkinter import messagebox
from database import register_user, check_login
from forgot_password import show_forgot_password_screen

def clear_window(root):
    for job in root.tk.splitlist(root.tk.call('after', 'info')):
        root.after_cancel(job)
    for widget in root.winfo_children():
        widget.destroy()

from customer_welcome import show_customer_welcome

def show_welcome_screen(root, email):
    show_customer_welcome(root, email, clear_window, show_login_screen)

def open_social_login(root, provider):
    social_window = tk.Toplevel(root)
    social_window.title(f"Sign in with {provider}")
    social_window.geometry("350x300")

    tk.Label(social_window, text=f"Sign in with {provider}", font=("Arial", 14, "bold")).pack(pady=15)
    tk.Label(social_window, text="Email").pack(pady=2)
    email_entry = tk.Entry(social_window, width=25)
    email_entry.pack(pady=5)

    tk.Label(social_window, text="Password").pack(pady=2)
    password_entry = tk.Entry(social_window, width=25, show="*")
    password_entry.pack(pady=5)

    def handle_social_login():
        email = email_entry.get()
        password = password_entry.get()
        if not email or not password:
            messagebox.showerror("Error", "All fields are required.", parent=social_window)
            return
        
        if check_login(email, password):
            social_window.destroy()
            show_welcome_screen(root, email)
        else:
            messagebox.showerror("Error", "Invalid email or password.", parent=social_window)

    tk.Button(social_window, text=f"Continue with {provider}", command=handle_social_login).pack(pady=20)

def show_login_screen(root, prefilled_email="customer@email.com", prefilled_password="customer1234"):
    clear_window(root)

    def set_demo(role):
        email_entry.delete(0, tk.END)
        password_entry.delete(0, tk.END)
        if role == "Customer":
            email_entry.insert(0, "customer@email.com")
            password_entry.insert(0, "customer1234")
        elif role == "Vendor":
            email_entry.insert(0, "vendor@email.com")
            password_entry.insert(0, "vendor1234")
        elif role == "Staff":
            email_entry.insert(0, "staff@email.com")
            password_entry.insert(0, "staff1234")
        elif role == "Partner":
            email_entry.insert(0, "partner@email.com")
            password_entry.insert(0, "partner1234")
        elif role == "Dispatcher":
            email_entry.insert(0, "dispatcher@email.com")
            password_entry.insert(0, "dispatcher1234")

    role_label = tk.Label(root, text="Choose Demo Account", font=("Arial", 12, "bold"))
    role_label.pack(pady=10)

    tk.Button(root, text="Customer", relief="raised", command=lambda: set_demo("Customer")).pack(pady=5)
    tk.Button(root, text="Vendor", relief="raised", command=lambda: set_demo("Vendor")).pack(pady=5)
    tk.Button(root, text="Staff", relief="raised", command=lambda: set_demo("Staff")).pack(pady=5)
    tk.Button(root, text="Partner", relief="raised", command=lambda: set_demo("Partner")).pack(pady=5)
    tk.Button(root, text="Dispatcher", relief="raised", command=lambda: set_demo("Dispatcher")).pack(pady=5)

    tk.Label(root, text="Email").pack(pady=5)
    email_entry = tk.Entry(root, width=30)
    email_entry.pack(pady=5)
    email_entry.insert(0, prefilled_email)

    tk.Label(root, text="Password").pack(pady=5)
    password_entry = tk.Entry(root, width=30, show="*")
    password_entry.pack(pady=5)
    password_entry.insert(0, prefilled_password)

    # Function to view password for 2 seconds
    def peek_password():
        password_entry.config(show="")
        root.after(2000, lambda: password_entry.config(show="*"))

    tk.Button(root, text="👁️", relief="raised", command=peek_password).pack(pady=2)

    def handle_login():
        email = email_entry.get()
        password = password_entry.get()
        if not email or not password:
            messagebox.showerror("Error", "All fields are required.")
            return
        
        if check_login(email, password):
            show_welcome_screen(root, email)
        else:
            messagebox.showerror("Error", "Invalid email or password.")

    login_button = tk.Button(root, text="Login", relief="raised", command=handle_login)
    login_button.pack(pady=10)

    tk.Button(root, text="Login with Google", relief="raised", command=lambda: open_social_login(root, "Google")).pack(pady=5)
    tk.Button(root, text="Login with Apple", relief="raised", command=lambda: open_social_login(root, "Apple")).pack(pady=5)

    create_account = tk.Button(root, text="Create Account", relief="raised", command=lambda: show_create_account_screen(root))
    create_account.pack(pady=5)

    forgot_password = tk.Button(root, text="Forgot Password?", relief="raised", command=lambda: show_forgot_password_screen(root, clear_window, show_login_screen))
    forgot_password.pack(pady=5)

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

    def register():
        email = reg_email.get()
        password = reg_pass.get()
        confirm = reg_confirm.get()

        if not email or not password or not confirm:
            messagebox.showerror("Error", "All fields are required.")
            return

        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match.")
            return

        success = register_user(email, password)
        if success:
            show_welcome_screen(root, email)
        else:
            messagebox.showerror("Error", "Email already exists in the database.")

    tk.Button(root, text="Register", relief="raised", command=register).pack(pady=20)
    tk.Button(root, text="Back to Login", relief="raised", command=lambda: show_login_screen(root)).pack(pady=5)