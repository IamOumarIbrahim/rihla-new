import tkinter as tk
from tkinter import messagebox
import theme as t
from config import MIN_PASSWORD_LENGTH
from database import update_password
import navigate

def show_reset_password_window(root, email):
    reset_win = tk.Toplevel(root)
    reset_win.title("Reset Password")
    reset_win.geometry("420x420")
    reset_win.configure(bg=t.CARD_BG)
    reset_win.resizable(False, False)

    # Center the popup window relative to root
    reset_win.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() // 2) - (420 // 2)
    y = root.winfo_y() + (root.winfo_height() // 2) - (420 // 2)
    reset_win.geometry(f"+{x}+{y}")

    form = tk.Frame(reset_win, bg=t.CARD_BG)
    form.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)

    tk.Label(form, text="Reset Password", font=(t.FONT, 20, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w")
    tk.Label(form, text="Enter your new secure password below", font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(2, 20))

    def _make_field(parent, label_text, show=""):
        tk.Label(parent, text=label_text, font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(10, 4))
        field = tk.Frame(parent, bg=t.FIELD_BG, highlightthickness=1, highlightbackground=t.BORDER, highlightcolor=t.PRIMARY)
        field.pack(fill=tk.X)
        entry = tk.Entry(field, font=(t.FONT, 11), bd=0, relief="flat", bg=t.FIELD_BG, fg=t.TEXT, insertbackground=t.TEXT, show=show)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, ipady=8)
        entry.bind("<FocusIn>", lambda e: field.config(highlightbackground=t.PRIMARY))
        entry.bind("<FocusOut>", lambda e: field.config(highlightbackground=t.BORDER))
        return field, entry

    new_field, new_pass_entry = _make_field(form, "NEW PASSWORD", show="*")
    
    def peek_password(entry_widget):
        entry_widget.config(show="")
        reset_win.after(2000, lambda: entry_widget.config(show="*"))

    tk.Button(new_field, text="\U0001F441\uFE0F", bd=0, relief="flat", bg=t.FIELD_BG,
              activebackground=t.FIELD_BG, cursor="hand2",
              command=lambda: peek_password(new_pass_entry)).pack(side=tk.RIGHT, padx=8)

    confirm_field, confirm_pass_entry = _make_field(form, "CONFIRM NEW PASSWORD", show="*")

    tk.Button(confirm_field, text="\U0001F441\uFE0F", bd=0, relief="flat", bg=t.FIELD_BG,
              activebackground=t.FIELD_BG, cursor="hand2",
              command=lambda: peek_password(confirm_pass_entry)).pack(side=tk.RIGHT, padx=8)

    def handle_reset():
        new_pass = new_pass_entry.get()
        confirm_pass = confirm_pass_entry.get()

        if not new_pass or not confirm_pass:
            messagebox.showerror("Error", "All fields are required.", parent=reset_win)
            return

        if new_pass != confirm_pass:
            messagebox.showerror("Error", "Passwords do not match.", parent=reset_win)
            return

        if len(new_pass) < MIN_PASSWORD_LENGTH:
            messagebox.showerror("Error", f"Password must be at least {MIN_PASSWORD_LENGTH} characters.", parent=reset_win)
            return

        update_password(email, new_pass)
        messagebox.showinfo("Success", "Password updated successfully!", parent=reset_win)
        reset_win.destroy()
        navigate.show_login(root, prefilled_email=email, prefilled_password=new_pass)

    update_btn = tk.Button(form, text="Update Password", font=(t.FONT, 11, "bold"), bd=0, relief="flat",
                           bg=t.PRIMARY, fg="white", activebackground=t.PRIMARY_HOVER, cursor="hand2",
                           command=handle_reset)
    update_btn.pack(fill=tk.X, pady=(25, 0), ipady=10)
    t.add_hover(update_btn, t.PRIMARY, t.PRIMARY_HOVER)