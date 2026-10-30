"""Writes a simple text PDF of a booking receipt, with no extra libraries."""

import os
import sys

PAGE_WIDTH, PAGE_HEIGHT = 595, 842  # A4 in points
MARGIN = 50


def default_download_dir():
    """The user's Downloads folder (follows a moved folder on Windows), or home."""
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
            value, _ = winreg.QueryValueEx(key, "{374DE290-123F-4565-9164-39C4925E467B}")
            path = os.path.expandvars(value)
            if os.path.isdir(path):
                return path
        except OSError:
            pass
    path = os.path.join(os.path.expanduser("~"), "Downloads")
    return path if os.path.isdir(path) else os.path.expanduser("~")


def _escape(text):
    text = str(text).encode("latin-1", "replace").decode("latin-1")
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_pdf(lines):
    """lines: list of (text, font_size, bold). An empty text adds a gap."""
    pages, current, y = [], [], PAGE_HEIGHT - MARGIN
    for text, size, bold in lines:
        step = size + 6
        if y - step < MARGIN:
            pages.append(current)
            current, y = [], PAGE_HEIGHT - MARGIN
        y -= step
        if text:
            font = "F2" if bold else "F1"
            current.append(f"BT /{font} {size} Tf {MARGIN} {y} Td ({_escape(text)}) Tj ET")
    pages.append(current)

    # Objects: 1 catalog, 2 page tree, 3-4 fonts, then a page + content pair per page.
    objects = [None, None,
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"]
    page_ids = []
    for commands in pages:
        stream = "\n".join(commands).encode("latin-1")
        content_id = len(objects) + 2
        page_ids.append(len(objects) + 1)
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
                       f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {content_id} 0 R >>".encode())
        objects.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    kids = " ".join(f"{i} 0 R" for i in page_ids)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode()

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    for offset in offsets:
        out += b"%010d 00000 n \n" % offset
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref)
    return bytes(out)


def save_pdf(lines, filename, folder=None):
    """Saves the PDF without overwriting an older file; returns its full path."""
    folder = folder or default_download_dir()
    stem, ext = os.path.splitext(filename)
    path, n = os.path.join(folder, filename), 1
    while os.path.exists(path):
        path = os.path.join(folder, f"{stem} ({n}){ext}")
        n += 1
    with open(path, "wb") as f:
        f.write(build_pdf(lines))
    return path
