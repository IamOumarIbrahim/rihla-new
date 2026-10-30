import os
import tkinter as tk
from PIL import Image, ImageTk

# Rihla logo drawn on the photo panels of the login, create account and forgot password screens
_LOGO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png"))
_raw_logo = None
if os.path.exists(_LOGO_PATH):
    try:
        _raw_logo = Image.open(_LOGO_PATH).convert("RGBA")
        bbox = _raw_logo.getchannel("A").getbbox()
        if bbox:
            _raw_logo = _raw_logo.crop(bbox)  # Trim the transparent padding around the artwork
    except OSError:
        _raw_logo = None


def draw_logo(canvas, w, h, center_y):
    """Draw the logo centred at (w / 2, center_y), sized to the panel but never stretched."""
    if not _raw_logo:
        return False

    img_w, img_h = _raw_logo.size
    target_w = min(w * 0.55, 340)
    target_h = min(h * 0.22, 190)
    scale = min(target_w / img_w, target_h / img_h)
    size = (max(int(img_w * scale), 1), max(int(img_h * scale), 1))

    # Keep a reference on the canvas so Tk does not garbage collect the image
    canvas._logo_photo = ImageTk.PhotoImage(_raw_logo.resize(size, Image.Resampling.LANCZOS))
    canvas.create_image(w / 2, center_y, anchor=tk.CENTER, image=canvas._logo_photo)
    return True
