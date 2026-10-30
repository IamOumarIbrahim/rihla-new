import tkinter as tk
import theme as t


class CapacityBar(tk.Frame):
    """Visual capacity bar.
    Filled with blue when full and white when empty.
    Next to it: simple text 'N remaining'.
    If N is 5 or less, adds additional text like 'Hurry up!'.
    """

    def __init__(self, parent, remaining=None, total=None, width=130, height=14, bg=None, **kwargs):
        self.bg_color = bg or (parent.cget("bg") if parent is not None else "#ffffff")
        super().__init__(parent, bg=self.bg_color, **kwargs)
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

        # Ratio: 1.0 when full (all seats available), 0.0 when empty (0 seats remaining)
        if total is None or total <= 0:
            ratio = 0.0
            remaining_val = 0
        elif remaining is None:
            ratio = 1.0
            remaining_val = total
        else:
            remaining_val = max(0, int(remaining))
            ratio = max(0.0, min(1.0, remaining_val / total))

        fill_w = int(self.bar_width * ratio)

        # "Filling up" only counts when some seats are really booked, not just because the event is small.
        has_bookings = total is not None and total > 0 and remaining_val < total
        if remaining_val <= 0:
            bar_color = "#e74c3c"
        elif has_bookings and (remaining_val <= 5 or ratio <= 0.25):
            bar_color = "#e67e22"
        else:
            bar_color = t.PRIMARY

        # White background (empty state)
        self.canvas.create_rectangle(
            0, 0, self.bar_width, self.bar_height,
            fill="#ffffff", outline=""
        )

        # Filled with blue when full / partially full
        if fill_w > 0:
            self.canvas.create_rectangle(
                0, 0, fill_w, self.bar_height,
                fill=bar_color, outline=""
            )

        # Clean border around the bar
        self.canvas.create_rectangle(
            0, 0, self.bar_width - 1, self.bar_height - 1,
            outline=t.PRIMARY, width=1
        )

        # Text next to the bar: "N of TOTAL remaining". "Hurry up!" only when it is really filling up.
        total_val = total if (total is not None and total > 0) else remaining_val
        count_text = f"{remaining_val} of {total_val} remaining"
        if suffix:
            text = f"{count_text} {suffix}"
            fg = t.TEXT_MUTED
        elif remaining_val <= 0:
            text = "0 remaining (Fully booked)"
            fg = "#e74c3c"
        elif has_bookings and (remaining_val <= 5 or ratio <= 0.25):
            text = f"{count_text} - Hurry up!"
            fg = "#e67e22"
        else:
            text = count_text
            fg = t.TEXT

        self.label.config(text=text, fg=fg)
