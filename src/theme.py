# colors and fonts for all the screens so they look the same
import os
import sys
import ctypes
import ctypes.util

# the fonts ship with the app (assets/fonts) so windows and linux look the same
FONT = "Noto Sans"
MONO = "Noto Sans Mono"

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fonts")
FONT_FILES = ["NotoSans-Regular.ttf", "NotoSans-Bold.ttf",
              "NotoSansMono-Regular.ttf", "NotoSansMono-Bold.ttf"]


# adds the font files to this program only, nothing is installed on the computer
# call it before tk.Tk() so tkinter can find the fonts
def load_fonts():
    fontconfig = None
    if sys.platform != "win32":
        name = ctypes.util.find_library("fontconfig")
        if name:
            fontconfig = ctypes.CDLL(name)

    for file_name in FONT_FILES:
        path = os.path.abspath(os.path.join(FONT_DIR, file_name))
        if not os.path.exists(path):
            continue
        try:
            if sys.platform == "win32":
                # 0x10 = FR_PRIVATE, only this program can use the font
                ctypes.windll.gdi32.AddFontResourceExW(path, 0x10, 0)
            elif fontconfig:
                fontconfig.FcConfigAppFontAddFile(None, path.encode("utf-8"))
        except Exception:
            # if it fails tkinter just uses its default font
            pass

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
