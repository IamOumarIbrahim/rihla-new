"""A venue name that works like a hyperlink: a click opens its Google Maps link in the default web browser."""
import tkinter as tk
import webbrowser
from tkinter import font as tkfont
from tkinter import messagebox

import theme as t

LINK_COLOR = "#1a73e8"
LINK_HOVER = "#174ea6"


def open_maps(url):
    """Opens the link in the default web browser."""
    try:
        opened = webbrowser.open(url)
    except Exception:
        opened = False
    if not opened:
        messagebox.showerror("Cannot open link", "The default web browser could not be opened.")


def venue_label(parent, text, maps_url, font=(t.FONT, 10), bg=None, fg=None, **kwargs):
    """Returns a Label with the venue name.
    With a maps_url it looks and works like a link (blue, underlined, hand cursor). Without one it is plain text.
    The caller places it with pack() or grid(), like any other label.
    """
    label = tk.Label(parent, text=text, font=font, bg=bg, fg=fg, **kwargs)
    url = (maps_url or "").strip()
    if not url:
        return label

    link_font = tkfont.Font(font=font)
    link_font.configure(underline=True)
    label.config(font=link_font, fg=LINK_COLOR, cursor="hand2")
    label._link_font = link_font  # keep a reference, so Tk does not delete the font

    label.bind("<Button-1>", lambda e: open_maps(url))
    label.bind("<Enter>", lambda e: label.config(fg=LINK_HOVER))
    label.bind("<Leave>", lambda e: label.config(fg=LINK_COLOR))
    return label
