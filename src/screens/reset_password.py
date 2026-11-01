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

    # put the popup in the middle of the main window
    reset_win.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() // 2) - (420 // 2)
    y = root.winfo_y() + (root.winfo_height() // 2) - (420 // 2)
    reset_win.geometry("+" + str(x) + "+" + str(y))

    form = tk.Frame(reset_win, bg=t.CARD_BG)
    form.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)

    tk.Label(form, text="Reset Password", font=(t.FONT, 20, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w")
    tk.Label(form, text="Enter your new secure password below", font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(2, 20))

    # new password field
    tk.Label(form, text="NEW PASSWORD", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(10, 4))
    new_field = tk.Frame(form, bg=t.FIELD_BG, highlightthickness=1, highlightbackground=t.BORDER, highlightcolor=t.PRIMARY)
    new_field.pack(fill=tk.X)
    new_pass_entry = tk.Entry(new_field, font=(t.FONT, 11), bd=0, relief="flat", bg=t.FIELD_BG, fg=t.TEXT, insertbackground=t.TEXT, show="*")
    new_pass_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, ipady=8)

    def new_focus_in(event):
        new_field.config(highlightbackground=t.PRIMARY)

    def new_focus_out(event):
        new_field.config(highlightbackground=t.BORDER)

    new_pass_entry.bind("<FocusIn>", new_focus_in)
    new_pass_entry.bind("<FocusOut>", new_focus_out)

    # shows the password for 2 seconds
    def peek_new():
        new_pass_entry.config(show="")

        def hide_again():
            new_pass_entry.config(show="*")
        reset_win.after(2000, hide_again)

    tk.Button(new_field, text="\U0001F441️", bd=0, relief="flat", bg=t.FIELD_BG,
              activebackground=t.FIELD_BG, cursor="hand2",
              command=peek_new).pack(side=tk.RIGHT, padx=8)

    # confirm field (same as above)
    tk.Label(form, text="CONFIRM NEW PASSWORD", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(10, 4))
    confirm_field = tk.Frame(form, bg=t.FIELD_BG, highlightthickness=1, highlightbackground=t.BORDER, highlightcolor=t.PRIMARY)
    confirm_field.pack(fill=tk.X)
    confirm_pass_entry = tk.Entry(confirm_field, font=(t.FONT, 11), bd=0, relief="flat", bg=t.FIELD_BG, fg=t.TEXT, insertbackground=t.TEXT, show="*")
    confirm_pass_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, ipady=8)

    def confirm_focus_in(event):
        confirm_field.config(highlightbackground=t.PRIMARY)

    def confirm_focus_out(event):
        confirm_field.config(highlightbackground=t.BORDER)

    confirm_pass_entry.bind("<FocusIn>", confirm_focus_in)
    confirm_pass_entry.bind("<FocusOut>", confirm_focus_out)

    def peek_confirm():
        confirm_pass_entry.config(show="")

        def hide_again():
            confirm_pass_entry.config(show="*")
        reset_win.after(2000, hide_again)

    tk.Button(confirm_field, text="\U0001F441️", bd=0, relief="flat", bg=t.FIELD_BG,
              activebackground=t.FIELD_BG, cursor="hand2",
              command=peek_confirm).pack(side=tk.RIGHT, padx=8)

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
            messagebox.showerror("Error", "Password must be at least " + str(MIN_PASSWORD_LENGTH) + " characters.", parent=reset_win)
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
