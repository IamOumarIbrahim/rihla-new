"""
digit_boxes.py  –  a row of one-digit boxes for codes that are digits only.

Used for the 16-digit ticket code (4 groups of 4) and the 5-digit vehicle
license (1 group of 5). Only 0-9 can get in: letters and symbols are ignored,
each digit jumps to the next box, Backspace walks back, and a pasted code is
spread over the boxes (spaces and dashes are dropped).

Usage:
    boxes = DigitBoxes(parent, groups=4, group_size=4, on_complete=validate)
    boxes.pack()
    code = boxes.get()          # "" up to "1234567890123456"
    boxes.is_complete()
    boxes.clear()
"""

import tkinter as tk
import theme as t


class DigitBoxes(tk.Frame):
    def __init__(self, parent, groups=1, group_size=5, font_size=16, box_width=2,
                 bg=t.CARD_BG, on_complete=None, on_change=None, initial=""):
        super().__init__(parent, bg=bg)
        self.on_complete = on_complete
        self.on_change = on_change
        self.boxes = []

        # Safety net for any other way text could get in (drag and drop, menus): one digit or nothing.
        vcmd = (self.register(lambda p: p == "" or (len(p) == 1 and p.isdigit())), "%P")

        for g in range(groups):
            if g > 0:
                tk.Label(self, text="-", font=(t.FONT, font_size), bg=bg, fg=t.TEXT_MUTED).pack(side=tk.LEFT, padx=4)
            for _ in range(group_size):
                box = tk.Entry(self, width=box_width, font=(t.FONT, font_size, "bold"), justify="center",
                               bg=t.FIELD_BG, fg=t.TEXT, relief="solid", bd=1, insertwidth=1,
                               highlightthickness=2, highlightbackground=t.BORDER, highlightcolor=t.PRIMARY,
                               validate="key", validatecommand=vcmd)
                box.pack(side=tk.LEFT, padx=2, ipady=4)
                box.bind("<KeyPress>", self._on_key)
                box.bind("<<Paste>>", self._on_paste)
                box.bind("<FocusIn>", lambda e: e.widget.select_range(0, tk.END))
                self.boxes.append(box)

        if initial:
            self.set(initial)

    # ---- public ------------------------------------------------------------
    def get(self):
        return "".join(b.get() for b in self.boxes)

    def is_complete(self):
        return len(self.get()) == len(self.boxes)

    def set(self, digits):
        digits = "".join(c for c in str(digits) if c.isdigit())[:len(self.boxes)]
        for i, box in enumerate(self.boxes):
            box.delete(0, tk.END)
            if i < len(digits):
                box.insert(0, digits[i])
        self._changed()

    def clear(self):
        self.set("")
        self.focus_first()

    def focus_first(self):
        self.boxes[0].focus_set()

    def set_error(self, on=True):
        """Red outline while the code is wrong, normal outline otherwise."""
        color = "#e74c3c" if on else t.BORDER
        for box in self.boxes:
            box.config(highlightbackground=color)

    # ---- internals ---------------------------------------------------------
    def _focus(self, index):
        index = max(0, min(index, len(self.boxes) - 1))
        self.boxes[index].focus_set()
        self.boxes[index].icursor(tk.END)

    def _changed(self):
        self.set_error(False)
        if self.on_change:
            self.on_change(self.get())
        if self.is_complete() and self.on_complete:
            self.on_complete(self.get())

    def _on_key(self, event):
        box = event.widget
        i = self.boxes.index(box)

        if event.char and event.char.isdigit() and len(event.char) == 1:
            box.delete(0, tk.END)
            box.insert(0, event.char)
            if i < len(self.boxes) - 1:
                self._focus(i + 1)
            self._changed()
            return "break"
        if event.keysym == "BackSpace":
            if box.get():
                box.delete(0, tk.END)
            elif i > 0:
                self.boxes[i - 1].delete(0, tk.END)
                self._focus(i - 1)
            self._changed()
            return "break"
        if event.keysym == "Delete":
            box.delete(0, tk.END)
            self._changed()
            return "break"
        if event.keysym == "Left":
            self._focus(i - 1)
            return "break"
        if event.keysym == "Right":
            self._focus(i + 1)
            return "break"
        if event.keysym == "Home":
            self._focus(0)
            return "break"
        if event.keysym == "End":
            self._focus(len(self.boxes) - 1)
            return "break"
        if event.state & 0x4 and event.keysym.lower() == "v":
            return self._on_paste(event)
        if event.keysym in ("Tab", "ISO_Left_Tab", "Return", "KP_Enter", "Escape"):
            return None  # let focus moves and Enter bindings work as usual
        if event.char:
            return "break"  # any other character (letters, symbols, spaces) never gets in
        return None

    def _on_paste(self, event):
        try:
            text = self.clipboard_get()
        except tk.TclError:
            return "break"
        digits = "".join(c for c in text if c.isdigit())
        if not digits:
            return "break"
        # A full code always fills from the first box; a shorter one fills from where the cursor is.
        start = 0 if len(digits) >= len(self.boxes) else self.boxes.index(event.widget)
        for offset, d in enumerate(digits[:len(self.boxes) - start]):
            box = self.boxes[start + offset]
            box.delete(0, tk.END)
            box.insert(0, d)
        self._focus(min(start + len(digits), len(self.boxes) - 1))
        self._changed()
        return "break"

    def bind_all_boxes(self, sequence, func):
        for box in self.boxes:
            box.bind(sequence, func, add="+")
