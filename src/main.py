import tkinter as tk

from database import init_db
import navigate


def main():
    init_db()

    root = tk.Tk()
    root.title("Rihla")

    # Always launch maximized
    try:
        root.state("zoomed")              # Windows / macOS
    except tk.TclError:
        root.attributes("-zoomed", True)  # Linux

    navigate.show_login(root)
    root.mainloop()


if __name__ == "__main__":
    main()