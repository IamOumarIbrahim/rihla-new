"""
icons.py  –  Lucide icon loader for Tkinter

Downloads SVG files from the lucide-static CDN on first use and caches them
to assets/icons/. Renders them with tksvg (a native Tk SVG extension).

Usage:
    from icons import get_icon
    img = get_icon("search", size=20, color="#2c3e50")   # returns tksvg.SvgImage
    tk.Label(parent, image=img).pack()
    # Keep a reference to img to prevent GC: widget.image = img

All icon names are from https://lucide-animated.com/  (lucide-static package).
"""

import os
import re
import urllib.request

try:
    import tksvg
    _TKSVG_AVAILABLE = True
except ImportError:
    _TKSVG_AVAILABLE = False

# ── paths ────────────────────────────────────────────────────────────────────
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_ICONS_DIR = os.path.join(_ROOT, "assets", "icons")
os.makedirs(_ICONS_DIR, exist_ok=True)

_CDN = "https://cdn.jsdelivr.net/npm/lucide-static@latest/icons/{name}.svg"

# ── in-process cache so the same (name, size, color) is created only once ────
_cache: dict[tuple, object] = {}


def _svg_path(name: str) -> str:
    return os.path.join(_ICONS_DIR, f"{name}.svg")


def _download(name: str) -> str:
    """Download icon SVG from CDN if not already cached on disk. Returns local path."""
    path = _svg_path(name)
    if not os.path.exists(path):
        url = _CDN.format(name=name)
        try:
            urllib.request.urlretrieve(url, path)
        except Exception as exc:
            # Return None-safe fallback path
            raise FileNotFoundError(f"Could not download lucide icon '{name}': {exc}")
    return path


def _recolor_svg(svg_text: str, color: str) -> str:
    """Inject stroke color into an SVG string (Lucide icons use stroke, not fill)."""
    # Replace existing stroke attributes on the root <svg> tag
    svg_text = re.sub(
        r'(<svg[^>]*)\bstroke="[^"]*"',
        lambda m: m.group(1) + f'stroke="{color}"',
        svg_text,
        count=1,
    )
    # If no stroke attribute at root level yet, add it
    if f'stroke="{color}"' not in svg_text:
        svg_text = re.sub(
            r"(<svg\b)",
            rf'\1 stroke="{color}"',
            svg_text,
            count=1,
        )
    return svg_text


def _set_size(svg_text: str, size: int) -> str:
    """Override width/height on the <svg> tag."""
    svg_text = re.sub(r'(<svg[^>]*)\bwidth="[^"]*"', lambda m: m.group(1) + f'width="{size}"', svg_text, count=1)
    svg_text = re.sub(r'(<svg[^>]*)\bheight="[^"]*"', lambda m: m.group(1) + f'height="{size}"', svg_text, count=1)
    if f'width="{size}"' not in svg_text:
        svg_text = re.sub(r"(<svg\b)", rf'\1 width="{size}" height="{size}"', svg_text, count=1)
    return svg_text


def get_icon(name: str, size: int = 18, color: str = "#2c3e50", master=None):
    """Return a tksvg.SvgImage (or None if tksvg unavailable / download failed).

    Parameters
    ----------
    name    : Lucide icon name, e.g. 'search', 'log-out', 'shopping-cart'
    size    : pixel size (square)
    color   : stroke color as hex string
    master  : Tkinter widget/root needed by tksvg (usually the root window)
    """
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
        with open(path, "r", encoding="utf-8") as f:
            svg_text = f.read()

        svg_text = _recolor_svg(svg_text, color)
        svg_text = _set_size(svg_text, size)

        # Write patched SVG to a temp string accepted by tksvg
        img = tksvg.SvgImage(data=svg_text, master=master, scaletowidth=size)
        _cache[key] = img
        return img
    except Exception:
        _cache[key] = None
        return None


def icon_button(parent, icon_name: str, text: str = "", size: int = 16,
                color: str = "#ffffff", bg: str = "#34495e", **btn_kwargs):
    """Create a tk.Button with a Lucide icon + optional text label.

    Falls back to text-only if tksvg is unavailable.
    """
    import tkinter as tk
    img = get_icon(icon_name, size=size, color=color, master=parent)
    if img:
        btn = tk.Button(parent, image=img, text=text, compound=tk.LEFT,
                        bg=bg, bd=0, relief="flat", **btn_kwargs)
        btn.image = img  # prevent GC
    else:
        btn = tk.Button(parent, text=text or icon_name, bg=bg,
                        bd=0, relief="flat", **btn_kwargs)
    return btn


# ── Convenience name map (Lucide icon name → semantic use) ───────────────────
ICONS = {
    "search":         "search",
    "settings":       "settings",
    "logout":         "log-out",
    "calendar":       "calendar",
    "clock":          "clock",
    "users":          "users",
    "user":           "user",
    "cart":           "shopping-cart",
    "payment":        "credit-card",
    "plus":           "plus",
    "close":          "x",
    "back":           "arrow-left",
    "ticket":         "ticket",
    "map_pin":        "map-pin",
    "star":           "star",
    "globe":          "globe",
    "filter":         "filter",
    "trash":          "trash-2",
    "check":          "check-circle",
    "alert":          "alert-circle",
    "refresh":        "refresh-cw",
    "copy":           "copy",
    "building":       "building",
    "truck":          "truck",
    "bar_chart":      "bar-chart-2",
    "bell":           "bell",
    "lock":           "lock",
    "eye":            "eye",
    "repeat":         "repeat",
    "tag":            "tag",
    "dollar":         "circle-dollar-sign",
    "list":           "list",
    "shield":         "shield-check",
    "scan":           "scan-line",
}
