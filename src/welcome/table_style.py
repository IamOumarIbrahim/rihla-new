# the look of all our tables: bold headings, a gear on the columns you can filter,
# a checkbox in the first column, rows in 2 colors and a small table with type and count
import tkinter as tk
from tkinter import ttk
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
    style.configure(TABLE_STYLE + ".Heading", font=(t.FONT, 10, "bold"), padding=(6, 6))


# heading of a column you can filter: the name, a gear and a dot when the filter is on
def heading_text(name, filter_active=False):
    text = name + "  " + GEAR
    if filter_active:
        text = text + " ●"
    return text


def stripe_tags(tree):
    tree.tag_configure("even", background=ROW_EVEN)
    tree.tag_configure("odd", background=ROW_ODD)
    tree.tag_configure("picked", background=ROW_SELECTED)
    tree.tag_configure("total", background=ROW_TOTAL, font=(t.FONT, 10, "bold"))


# small table with one row for every value and how many times it is there, and a total row
# items is a list of values (like the vehicle type of every vehicle)
def build_count_table(parent, items, label="Vehicle Type"):
    style_tables()

    # count every value
    counts = {}
    for value in items:
        if value in counts:
            counts[value] += 1
        else:
            counts[value] = 1

    # sort by name (insertion sort, not case sensitive)
    names = []
    for value in counts:
        names.append(value)
    for i in range(1, len(names)):
        temp = names[i]
        j = i - 1
        while j >= 0 and str(names[j]).lower() > str(temp).lower():
            names[j + 1] = names[j]
            j -= 1
        names[j + 1] = temp

    frame = tk.Frame(parent, bg=t.CARD_BG, bd=1, relief="solid", highlightbackground=t.BORDER)
    tree = ttk.Treeview(frame, columns=("value", "count"), show="headings", height=len(counts) + 1,
                        style=TABLE_STYLE, selectmode="none")
    stripe_tags(tree)
    tree.heading("value", text=label, anchor="w")
    tree.heading("count", text="Count")
    tree.column("value", width=220, minwidth=220, anchor="w", stretch=False)
    tree.column("count", width=80, minwidth=80, anchor="center", stretch=False)

    total = 0
    for i in range(len(names)):
        if i % 2:
            tag = "odd"
        else:
            tag = "even"
        tree.insert("", tk.END, values=(names[i], counts[names[i]]), tags=(tag,))
        total = total + counts[names[i]]
    tree.insert("", tk.END, values=("Total", total), tags=("total",))
    tree.pack()
    return frame
