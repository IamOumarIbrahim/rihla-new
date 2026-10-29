import tkinter as tk
from database import init_db
from screens import show_login_screen

# Initialize SQLite database
init_db()

# Main window
root = tk.Tk()
root.title("Rihla")
root.geometry("1920x1080")

# Start with the login screen
show_login_screen(root)

root.mainloop()