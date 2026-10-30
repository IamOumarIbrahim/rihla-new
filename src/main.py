import socket
socket.setdefaulttimeout(3)
import tkinter as tk

import navigate


def main():

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