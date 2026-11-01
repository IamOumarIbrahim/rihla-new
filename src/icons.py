# loads lucide icons for tkinter
# it gets the svg files from the lucide-static cdn the first time and saves them in assets/icons/
# then tksvg draws them
#
#   from icons import get_icon
#   img = get_icon("search", size=20, color="#2c3e50")
#   tk.Label(parent, image=img).pack()
#   keep img somewhere (widget.image = img) or it disapears
#
# icon names are from https://lucide-animated.com/  (lucide-static package)

import os
import re
import urllib.request

try:
    import tksvg
    _TKSVG_AVAILABLE = True
except ImportError:
    _TKSVG_AVAILABLE = False

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_ICONS_DIR = os.path.join(_ROOT, "assets", "icons")
os.makedirs(_ICONS_DIR, exist_ok=True)

_CDN = "https://cdn.jsdelivr.net/npm/lucide-static@latest/icons/{name}.svg"

# True = get missing icons from the cdn, False = never use the network
ALLOW_DOWNLOADS = False

# so the same (name, size, color) is only made once
_cache = {}


# True = emoji next to the labels instead of svg icons (no downloads and no tksvg)
USE_EMOJI = True

EMOJI = {
    "search":    "\U0001F50D",
    "filter":    "\u2699",
    "star":      "\u2B50",
    "map_pin":   "\U0001F4CD",
    "repeat":    "\U0001F501",
    "users":     "\U0001F465",
    "user":      "\U0001F464",
    "copy":      "\U0001F4CB",
    "close":     "\u2716",
    "back":      "\u2B05",
    "calendar":  "\U0001F4C5",
    "clock":     "\U0001F552",
    "truck":     "\U0001F690",
    "shield":    "\U0001F6E1",
    "plus":      "\u2795",
    "payment":   "\U0001F4B3",
    "cart":      "\U0001F6D2",
    "ticket":    "\U0001F39F",
    "check":     "\u2705",
    "alert":     "\u26A0",
    "trash":     "\U0001F5D1",
    "refresh":   "\U0001F504",
    "globe":     "\U0001F30D",
    "bell":      "\U0001F514",
    "lock":      "\U0001F512",
    "tag":       "\U0001F3F7",
    "dollar":    "\U0001F4B0",
    "list":      "\U0001F4CB",
    "building":  "\U0001F3E2",
    "bar_chart": "\U0001F4CA",
    "eye":       "\U0001F441",
    "logout":    "\U0001F6AA",
    "settings":  "\u2699",
    "scan":      "\U0001F4F7",
    "wave":      "\U0001F44B",
    "sparkles":  "\u2728",
    "compass":   "\U0001F9ED",
    "chat":      "\U0001F4AC",
    "stadium":   "\U0001F3DF",
    "edit":      "\u270F",
    "car":       "\U0001F697",
    "wrench":    "\U0001F527",
    "cross":     "\u274C",
    "handshake": "\U0001F91D",
    "picture":   "\U0001F5BC",
}


# emoji for an icon name ("" if emoji mode is off or the name is unknown)
def emoji(name):
    if not USE_EMOJI:
        return ""
    return EMOJI.get(name, "")


def _svg_path(name):
    return os.path.join(_ICONS_DIR, name + ".svg")


# downloads the svg from the cdn if we dont have it yet, gives back the local path
def _download(name):
    path = _svg_path(name)
    if not os.path.exists(path):
        if not ALLOW_DOWNLOADS:
            raise FileNotFoundError("Icon '" + name + "' is not cached and downloads are disabled.")
        url = _CDN.format(name=name)
        try:
            urllib.request.urlretrieve(url, path)
        except Exception as exc:
            raise FileNotFoundError("Could not download lucide icon '" + name + "': " + str(exc))
    return path


# puts the stroke color in the svg (lucide icons use stroke not fill)
def _recolor_svg(svg_text, color):
    # change the stroke that is already on the <svg> tag
    svg_text = re.sub(r'(<svg[^>]*)\bstroke="[^"]*"', r'\1stroke="' + color + '"', svg_text, count=1)
    # no stroke there yet so add one
    if ('stroke="' + color + '"') not in svg_text:
        svg_text = re.sub(r"(<svg\b)", r'\1 stroke="' + color + '"', svg_text, count=1)
    return svg_text


# sets width and height on the <svg> tag
def _set_size(svg_text, size):
    size = str(size)
    svg_text = re.sub(r'(<svg[^>]*)\bwidth="[^"]*"', r'\1width="' + size + '"', svg_text, count=1)
    svg_text = re.sub(r'(<svg[^>]*)\bheight="[^"]*"', r'\1height="' + size + '"', svg_text, count=1)
    if ('width="' + size + '"') not in svg_text:
        svg_text = re.sub(r"(<svg\b)", r'\1 width="' + size + '" height="' + size + '"', svg_text, count=1)
    return svg_text


# gives back a tksvg.SvgImage or None (no tksvg or the download failed)
# name is the lucide name like 'search' or 'log-out', size in pixels (square), color is a hex string
# master is the tk widget tksvg needs (normally the root)
def get_icon(name, size=18, color="#2c3e50", master=None):
    if USE_EMOJI:
        return None

    if not _TKSVG_AVAILABLE:
        return None

    key = (name, size, color)
    if key in _cache:
        return _cache[key]

    try:
        path = _download(name)
    except FileNotFoundError:
        _cache[key] = None
        return None

    try:
        f = open(path, "r", encoding="utf-8")
        svg_text = f.read()
        f.close()

        svg_text = _recolor_svg(svg_text, color)
        svg_text = _set_size(svg_text, size)

        img = tksvg.SvgImage(data=svg_text, master=master, scaletowidth=size)
        _cache[key] = img
        return img
    except Exception:
        _cache[key] = None
        return None
