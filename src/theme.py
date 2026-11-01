# colors and fonts for all the screens so they look the same

FONT = "Segoe UI"

DARK = "#2c3e50"
DARK_SOFT = "#34495e"
PRIMARY = "#2980b9"
PRIMARY_HOVER = "#2471a3"
ACCENT = "#f39c12"

PAGE_BG = "#ecf0f1"
CARD_BG = "#ffffff"
FIELD_BG = "#f8f9fa"
BORDER = "#dcdde1"

TEXT = "#2c3e50"
TEXT_MUTED = "#7f8c8d"

CHIP_BG = "#ecf0f1"
CHIP_HOVER = "#dfe6e9"


# changes the background of a widget while the mouse is on it
def add_hover(widget, normal, hover):
    def on_enter(event):
        widget.config(bg=hover)

    def on_leave(event):
        widget.config(bg=normal)

    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)
