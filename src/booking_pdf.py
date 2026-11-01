# makes a simple pdf of the booking receipt (only text, no extra libraries)

import os
import sys

PAGE_WIDTH = 595   # A4 in points
PAGE_HEIGHT = 842
MARGIN = 50


# the Downloads folder of the user (also if it was moved on windows), otherwise home
def default_download_dir():
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
            value, kind = winreg.QueryValueEx(key, "{374DE290-123F-4565-9164-39C4925E467B}")
            path = os.path.expandvars(value)
            if os.path.isdir(path):
                return path
        except OSError:
            pass
    path = os.path.join(os.path.expanduser("~"), "Downloads")
    if os.path.isdir(path):
        return path
    return os.path.expanduser("~")


def _escape(text):
    text = str(text).encode("latin-1", "replace").decode("latin-1")
    text = text.replace("\\", "\\\\")
    text = text.replace("(", "\\(")
    text = text.replace(")", "\\)")
    return text


# lines is a list of (text, font_size, bold), empty text just leaves a gap
def build_pdf(lines):
    pages = []
    current = []
    y = PAGE_HEIGHT - MARGIN
    for text, size, bold in lines:
        step = size + 6
        if y - step < MARGIN:
            # page is full start a new one
            pages.append(current)
            current = []
            y = PAGE_HEIGHT - MARGIN
        y -= step
        if text:
            if bold:
                font = "F2"
            else:
                font = "F1"
            current.append("BT /" + font + " " + str(size) + " Tf " + str(MARGIN) + " " + str(y)
                           + " Td (" + _escape(text) + ") Tj ET")
    pages.append(current)

    # objects: 1 catalog, 2 page tree, 3 and 4 fonts, then a page and its content for every page
    objects = [None, None,
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"]
    page_ids = []
    for commands in pages:
        stream = "\n".join(commands).encode("latin-1")
        content_id = len(objects) + 2
        page_ids.append(len(objects) + 1)
        page = ("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 " + str(PAGE_WIDTH) + " " + str(PAGE_HEIGHT) + "] "
                + "/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents " + str(content_id) + " 0 R >>")
        objects.append(page.encode())
        objects.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    kids = ""
    for i in page_ids:
        if kids != "":
            kids = kids + " "
        kids = kids + str(i) + " 0 R"
    objects[1] = ("<< /Type /Pages /Kids [" + kids + "] /Count " + str(len(page_ids)) + " >>").encode()

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    number = 1
    for body in objects:
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
        number += 1
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    for offset in offsets:
        out += b"%010d 00000 n \n" % offset
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref)
    return bytes(out)


# saves the pdf and never writes over an older file, gives back the full path
def save_pdf(lines, filename, folder=None):
    if not folder:
        folder = default_download_dir()
    stem, ext = os.path.splitext(filename)
    path = os.path.join(folder, filename)
    n = 1
    while os.path.exists(path):
        path = os.path.join(folder, stem + " (" + str(n) + ")" + ext)
        n += 1
    f = open(path, "wb")
    f.write(build_pdf(lines))
    f.close()
    return path
