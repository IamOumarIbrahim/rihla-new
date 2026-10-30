"""Look shared by the app's data tables: bold headings, a gear on filterable columns,
a checkbox first column, striped rows, and a small type/count summary table."""
import tkinter as tk
from tkinter import ttk
from collections import Counter
import theme as t

GEAR = "⚙"
CHECKED = "☑"
UNCHECKED = "☐"

ROW_EVEN = "#ffffff"
ROW_ODD = "#f4f6f7"
ROW_SELECTED = "#d6eaf8"
ROW_TOTAL = "#e5e8e8"

TABLE_STYLE = "Dispatch.Treeview"


def style_tables():
    style = ttk.Style()
    style.configure(TABLE_STYLE, rowheight=28, font=(t.FONT, 10), background=ROW_EVEN, fieldbackground=ROW_EVEN)
    style.configure(f"{TABLE_STYLE}.Heading", font=(t.FONT, 10, "bold"), padding=(6, 6))


def heading_text(name, filter_active=False):
    """Heading of a filterable column: the name, a gear, and a dot while a filter is on."""
    return f"{name}  {GEAR}{' ●' if filter_active else ''}"


def stripe_tags(tree):
    tree.tag_configure("even", background=ROW_EVEN)
    tree.tag_configure("odd", background=ROW_ODD)
    tree.tag_configure("picked", background=ROW_SELECTED)
    tree.tag_configure("total", background=ROW_TOTAL, font=(t.FONT, 10, "bold"))


def build_count_table(parent, items, label="Vehicle Type"):
    """Mini table with one row per value and how often it appears, plus a total row.
    `items` is a list of values (for example the vehicle type of every vehicle)."""
    style_tables()
    counts = Counter(items)
    frame = tk.Frame(parent, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
    tree = ttk.Treeview(frame, columns=("value", "count"), show="headings", height=len(counts) + 1,
                        style=TABLE_STYLE, selectmode="none")
    stripe_tags(tree)
    tree.heading("value", text=label, anchor="w")
    tree.heading("count", text="Count")
    tree.column("value", width=220, minwidth=220, anchor="w", stretch=False)
    tree.column("count", width=80, minwidth=80, anchor="center", stretch=False)
    for i, (value, n) in enumerate(sorted(counts.items(), key=lambda kv: str(kv[0]).lower())):
        tree.insert("", tk.END, values=(value, n), tags=("odd" if i % 2 else "even",))
    tree.insert("", tk.END, values=("Total", sum(counts.values())), tags=("total",))
    tree.pack()
    return frame
