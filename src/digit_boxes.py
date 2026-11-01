# a row of boxes with one digit each, for codes that are only numbers
# we use it for the 16 digit ticket code (4 groups of 4) and the 5 digit vehicle license (1 group of 5)
# only 0-9 can go in, other keys are ignored  every digit jumps to the next box and backspace goes back
# pasting a code fills the boxes (spaces and dashes are removed)
#
# how to use it:
#   boxes = DigitBoxes(parent, groups=4, group_size=4, on_complete=validate)
#   boxes.pack()
#   code = boxes.get()     "" up to "1234567890123456"
#   boxes.is_complete()
#   boxes.clear()

import tkinter as tk
import theme as t


class DigitBoxes(tk.Frame):
    def __init__(self, parent, groups=1, group_size=5, font_size=16, box_width=2,
                 bg=t.CARD_BG, on_complete=None, on_change=None, initial=""):
        tk.Frame.__init__(self, parent, bg=bg)
        self.on_complete = on_complete
        self.on_change = on_change
        self.boxes = []

        # in case text gets in some other way (drag and drop, menus), only one digit or nothing
        vcmd = (self.register(self._allowed), "%P")

        for g in range(groups):
            if g > 0:
                tk.Label(self, text="-", font=(t.FONT, font_size), bg=bg, fg=t.TEXT_MUTED).pack(side=tk.LEFT, padx=4)
            for k in range(group_size):
                box = tk.Entry(self, width=box_width, font=(t.FONT, font_size, "bold"), justify="center",
                               bg=t.FIELD_BG, fg=t.TEXT, relief="solid", bd=1, insertwidth=1,
                               highlightthickness=2, highlightbackground=t.BORDER, highlightcolor=t.PRIMARY,
                               validate="key", validatecommand=vcmd)
                box.pack(side=tk.LEFT, padx=2, ipady=4)
                box.bind("<KeyPress>", self._on_key)
                box.bind("<<Paste>>", self._on_paste)
                box.bind("<FocusIn>", self._select_all)
                self.boxes.append(box)

        if initial:
            self.set(initial)

    def _allowed(self, p):
        if p == "":
            return True
        if len(p) == 1 and p.isdigit():
            return True
        return False

    def _select_all(self, event):
        event.widget.select_range(0, tk.END)

    def get(self):
        code = ""
        for b in self.boxes:
            code = code + b.get()
        return code

    def is_complete(self):
        return len(self.get()) == len(self.boxes)

    def set(self, digits):
        only_digits = ""
        for c in str(digits):
            if c.isdigit():
                only_digits = only_digits + c
        only_digits = only_digits[:len(self.boxes)]
        for i in range(len(self.boxes)):
            box = self.boxes[i]
            box.delete(0, tk.END)
            if i < len(only_digits):
                box.insert(0, only_digits[i])
        self._changed()

    def clear(self):
        self.set("")
        self.focus_first()

    def focus_first(self):
        self.boxes[0].focus_set()

    # red border when the code is wrong, normal border otherwise
    def set_error(self, on=True):
        if on:
            color = "#e74c3c"
        else:
            color = t.BORDER
        for box in self.boxes:
            box.config(highlightbackground=color)

    def _focus(self, index):
        if index > len(self.boxes) - 1:
            index = len(self.boxes) - 1
        if index < 0:
            index = 0
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
            return None  # tab and enter keep working normaly
        if event.char:
            return "break"  # every other character (letters, symbols, spaces) is blocked
        return None

    def _on_paste(self, event):
        try:
            text = self.clipboard_get()
        except tk.TclError:
            return "break"
        digits = ""
        for c in text:
            if c.isdigit():
                digits = digits + c
        if not digits:
            return "break"
        # a full code always starts at the first box, a shorter one starts where the cursor is
        if len(digits) >= len(self.boxes):
            start = 0
        else:
            start = self.boxes.index(event.widget)
        part = digits[:len(self.boxes) - start]
        for offset in range(len(part)):
            box = self.boxes[start + offset]
            box.delete(0, tk.END)
            box.insert(0, part[offset])
        last = start + len(digits)
        if last > len(self.boxes) - 1:
            last = len(self.boxes) - 1
        self._focus(last)
        self._changed()
        return "break"

    def bind_all_boxes(self, sequence, func):
        for box in self.boxes:
            box.bind(sequence, func, add="+")
