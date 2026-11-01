import socket
socket.setdefaulttimeout(3)
import tkinter as tk

import navigate


def main():

    root = tk.Tk()
    root.title("Rihla")

    # always open the window maximized
    try:
        root.state("zoomed")  # windows / mac
    except tk.TclError:
        root.attributes("-zoomed", True)  # linux

    navigate.show_login(root)
    root.mainloop()


if __name__ == "__main__":
    main()
