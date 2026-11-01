# venue name that works like a link, clicking it opens the google maps link in the browser
import tkinter as tk
import webbrowser
from tkinter import font as tkfont
from tkinter import messagebox

import theme as t

LINK_COLOR = "#1a73e8"
LINK_HOVER = "#174ea6"


def open_maps(url):
    try:
        opened = webbrowser.open(url)
    except Exception:
        opened = False
    if not opened:
        messagebox.showerror("Cannot open link", "The default web browser could not be opened.")


# label with the venue name, with a maps_url it looks like a link (blue, underlined, hand cursor)
# without one its just normal text  the caller does pack() or grid() on it
def venue_label(parent, text, maps_url, font=(t.FONT, 10), bg=None, fg=None, **kwargs):
    label = tk.Label(parent, text=text, font=font, bg=bg, fg=fg, **kwargs)
    if maps_url:
        url = maps_url.strip()
    else:
        url = ""
    if not url:
        return label

    link_font = tkfont.Font(font=font)
    link_font.configure(underline=True)
    label.config(font=link_font, fg=LINK_COLOR, cursor="hand2")
    label._link_font = link_font  # keep it or tk deletes the font

    def on_click(event):
        open_maps(url)

    def on_enter(event):
        label.config(fg=LINK_HOVER)

    def on_leave(event):
        label.config(fg=LINK_COLOR)

    label.bind("<Button-1>", on_click)
    label.bind("<Enter>", on_enter)
    label.bind("<Leave>", on_leave)
    return label
