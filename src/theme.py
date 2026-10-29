"""Shared colors and fonts so every screen looks consistent."""

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


def add_hover(widget, normal, hover):
    """Change a widget's background while the mouse is over it."""
    widget.bind("<Enter>", lambda e: widget.config(bg=hover))
    widget.bind("<Leave>", lambda e: widget.config(bg=normal))