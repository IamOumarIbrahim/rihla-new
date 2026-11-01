# pictures of the events for the cards and the event page
#   load_image(event_id)    gets the picture from the server (saved in _cache) or None
#   CoverImage              widget that fills all its space with the picture (cropped, not stretched)
#   build_card_shell(...)   splits a card in a text part (returned) and a picture part on the right
#   encode_image_file(path) turns the file the vendor picked into base64 jpeg text for the server
# needs Pillow:  pip install pillow
import base64
import io
import tkinter as tk

import theme as t
from api_client import get_event_image

try:
    from PIL import Image, ImageOps, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

_cache = {}  # event_id -> picture, or None if the event has no picture


# forget the saved picture (after the vendor changed it)
def forget(event_id):
    if event_id in _cache:
        del _cache[event_id]


def load_image(event_id):
    if not PIL_AVAILABLE:
        return None
    if event_id in _cache:
        return _cache[event_id]
    img = None
    try:
        data = get_event_image(event_id)
        if data:
            img = Image.open(io.BytesIO(data))
            img.load()
            img = img.convert("RGB")
    except Exception:
        img = None
    _cache[event_id] = img
    return img


# reads a picture file and gives it back as base64 jpeg text (turned the right way, smaller if its huge)
def encode_image_file(path, max_side=1400):
    if not PIL_AVAILABLE:
        raise RuntimeError("Pillow is not installed. Run: python -m pip install pillow")
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "LA", "P"):
        # white background because jpeg has no transparency
        img = img.convert("RGBA")
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1])
        img = background
    else:
        img = img.convert("RGB")
    img.thumbnail((max_side, max_side), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85, optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")


# fills the whole frame with the picture, scaled to cover and cut in the middle, never stretched
class CoverImage(tk.Frame):

    def __init__(self, parent, pil_image=None, **kwargs):
        if "bg" not in kwargs:
            kwargs["bg"] = t.CHIP_BG
        tk.Frame.__init__(self, parent, **kwargs)
        self._pil = pil_image
        self._photo = None
        self._last_size = (0, 0)
        self._label = tk.Label(self, bg=kwargs["bg"], bd=0)
        if pil_image is None:
            self._label.config(text="\U0001F5BC", font=(t.FONT, 28), fg=t.TEXT_MUTED)
        self._label.place(x=0, y=0, relwidth=1, relheight=1)
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        if self._pil is None or event.width < 20 or event.height < 20:
            return
        size = (event.width, event.height)
        if size == self._last_size:
            return
        self._last_size = size
        fitted = ImageOps.fit(self._pil, size, Image.LANCZOS, centering=(0.5, 0.5))
        self._photo = ImageTk.PhotoImage(fitted)
        self._label.config(image=self._photo)


# splits a card frame in a text part (returned) and a picture part on the right
def build_card_shell(outer, event_id, bg=None, text_weight=1, image_weight=1):
    if not bg:
        bg = t.CARD_BG
    if text_weight == image_weight:
        outer.columnconfigure(0, weight=text_weight, uniform="half")
        outer.columnconfigure(1, weight=image_weight, uniform="half")
    else:
        outer.columnconfigure(0, weight=text_weight)
        outer.columnconfigure(1, weight=image_weight)
    outer.rowconfigure(0, weight=1)
    text_area = tk.Frame(outer, bg=bg)
    text_area.grid(row=0, column=0, sticky="nsew")
    CoverImage(outer, load_image(event_id)).grid(row=0, column=1, sticky="nsew")
    return text_area
