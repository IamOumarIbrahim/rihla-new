import os
import tkinter as tk
from PIL import Image, ImageTk

# Rihla logo on the photo side of the login, create account and forgot password screens
_LOGO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png"))
_raw_logo = None
if os.path.exists(_LOGO_PATH):
    try:
        _raw_logo = Image.open(_LOGO_PATH).convert("RGBA")
        bbox = _raw_logo.getchannel("A").getbbox()
        if bbox:
            # cut off the empty see through border
            _raw_logo = _raw_logo.crop(bbox)
    except OSError:
        _raw_logo = None


# draws the logo in the middle at (w / 2, center_y), fits the panel but never stretched
def draw_logo(canvas, w, h, center_y):
    if not _raw_logo:
        return False

    img_w, img_h = _raw_logo.size
    target_w = w * 0.55
    if target_w > 340:
        target_w = 340
    target_h = h * 0.22
    if target_h > 190:
        target_h = 190

    scale = target_w / img_w
    if target_h / img_h < scale:
        scale = target_h / img_h
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)
    if new_w < 1:
        new_w = 1
    if new_h < 1:
        new_h = 1

    # keep the image on the canvas or tk throws it away
    canvas._logo_photo = ImageTk.PhotoImage(_raw_logo.resize((new_w, new_h), Image.Resampling.LANCZOS))
    canvas.create_image(w / 2, center_y, anchor=tk.CENTER, image=canvas._logo_photo)
    return True
