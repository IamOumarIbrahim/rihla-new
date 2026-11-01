import tkinter as tk
import theme as t


# bar that shows the seats left
# blue when all seats are free and white when there are none, the text next to it says
# 'N of TOTAL remaining' and when its filling up it adds 'Hurry up!'
class CapacityBar(tk.Frame):

    def __init__(self, parent, remaining=None, total=None, width=130, height=14, bg=None, **kwargs):
        if bg:
            self.bg_color = bg
        elif parent is not None:
            self.bg_color = parent.cget("bg")
        else:
            self.bg_color = "#ffffff"
        tk.Frame.__init__(self, parent, bg=self.bg_color, **kwargs)
        self.bar_width = width
        self.bar_height = height
        self.remaining = remaining
        self.total = total

        self.canvas = tk.Canvas(
            self,
            width=self.bar_width,
            height=self.bar_height,
            bg="#ffffff",
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(side=tk.LEFT, pady=2)

        self.label = tk.Label(
            self,
            text="",
            font=(t.FONT, 9, "bold"),
            bg=self.bg_color,
            fg=t.TEXT
        )
        self.label.pack(side=tk.LEFT, padx=(8, 0))

        if remaining is not None and total is not None:
            self.set_capacity(remaining, total)

    def set_capacity(self, remaining, total, suffix=""):
        self.remaining = remaining
        self.total = total
        self.canvas.delete("all")

        # ratio = remaining / total  (1.0 all seats free, 0.0 nothing left)
        if total is None or total <= 0:
            ratio = 0.0
            remaining_val = 0
        elif remaining is None:
            ratio = 1.0
            remaining_val = total
        else:
            remaining_val = int(remaining)
            if remaining_val < 0:
                remaining_val = 0
            ratio = remaining_val / total
            if ratio > 1.0:
                ratio = 1.0
            if ratio < 0.0:
                ratio = 0.0

        fill_w = int(self.bar_width * ratio)

        # its only filling up when seats are really booked, a small event alone doesnt count
        has_bookings = total is not None and total > 0 and remaining_val < total
        filling_up = has_bookings and (remaining_val <= 5 or ratio <= 0.25)
        if remaining_val <= 0:
            bar_color = "#e74c3c"
        elif filling_up:
            bar_color = "#e67e22"
        else:
            bar_color = t.PRIMARY

        # white background
        self.canvas.create_rectangle(
            0, 0, self.bar_width, self.bar_height,
            fill="#ffffff", outline=""
        )

        # the filled part
        if fill_w > 0:
            self.canvas.create_rectangle(
                0, 0, fill_w, self.bar_height,
                fill=bar_color, outline=""
            )

        # border
        self.canvas.create_rectangle(
            0, 0, self.bar_width - 1, self.bar_height - 1,
            outline=t.PRIMARY, width=1
        )

        # Text next to the bar

        if total is not None and total > 0:
            total_val = total
        else:
            total_val = remaining_val
        count_text = str(remaining_val) + " of " + str(total_val) + " remaining"
        if suffix:
            text = count_text + " " + suffix
            fg = t.TEXT_MUTED
        elif remaining_val <= 0:
            text = "0 remaining (Fully booked)"
            fg = "#e74c3c"
        elif filling_up:
            text = count_text + " - Hurry up!"
            fg = "#e67e22"
        else:
            text = count_text
            fg = t.TEXT

        self.label.config(text=text, fg=fg)
