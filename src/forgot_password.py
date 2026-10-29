import tkinter as tk
from tkinter import messagebox
from database import get_password_by_email

def edit_distance(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2 + 1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]

def show_forgot_password_screen(root, clear_window_func, show_login_func):
    clear_window_func(root)

    tk.Label(root, text="Forgot Password", font=("Arial", 14, "bold")).pack(pady=20)

    tk.Label(root, text="Enter Email").pack(pady=5)
    email_entry = tk.Entry(root, width=30)
    email_entry.pack(pady=5)

    tk.Label(root, text="Best Guess Password").pack(pady=5)
    guess_entry = tk.Entry(root, width=30, show="*")
    guess_entry.pack(pady=5)

    # Status label for inline messages instead of a popup
    status_label = tk.Label(root, text="", font=("Arial", 11, "bold"))
    status_label.pack(pady=5)

    def verify_guess():
        email = email_entry.get()
        guess = guess_entry.get()

        if not email or not guess:
            messagebox.showerror("Error", "All fields are required.")
            return

        stored_password = get_password_by_email(email)
        if not stored_password:
            messagebox.showerror("Error", "Email not found in database.")
            return

        distance = edit_distance(guess, stored_password)

        if distance <= 3:
            status_label.config(text="Close guess! Recovering password...", fg="green")

            def delayed_action():
                show_login_func(root, prefilled_email=email, prefilled_password=stored_password)

            root.after(3000, delayed_action)
        else:
            status_label.config(text="")
            messagebox.showerror("Error", "Password guess is too far off.")

    tk.Button(root, text="Submit Guess", relief="raised", command=verify_guess).pack(pady=20)
    tk.Button(root, text="Back to Login", relief="raised", command=lambda: show_login_func(root)).pack(pady=5)