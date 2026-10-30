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

        # White background (empty state)
        self.canvas.create_rectangle(
            0, 0, self.bar_width, self.bar_height,
            fill="#ffffff", outline=""
        )

        # Filled with blue when full / partially full
        if fill_w > 0:
            self.canvas.create_rectangle(
                0, 0, fill_w, self.bar_height,
                fill=t.PRIMARY, outline=""
            )

        # Clean border around the bar
        self.canvas.create_rectangle(
            0, 0, self.bar_width - 1, self.bar_height - 1,
            outline=t.PRIMARY, width=1
        )

        # Simple text next to it: N remaining
        # If N is 5 or less, add additional text: "Hurry up!"
        if suffix:
            text = f"{remaining_val} remaining {suffix}"
            fg = t.TEXT_MUTED
        elif remaining_val <= 0:
            text = "0 remaining (Fully booked)"
            fg = "#e74c3c"
        elif remaining_val <= 5:
            text = f"{remaining_val} remaining - Hurry up!"
            fg = "#e67e22"
        else:
            text = f"{remaining_val} remaining"
            fg = t.TEXT

        self.label.config(text=text, fg=fg)
