def clear_window(root):
    """Cancel timers, drop global mouse-wheel bindings, destroy all widgets."""
    for job in root.tk.splitlist(root.tk.call('after', 'info')):
        root.after_cancel(job)

    # Welcome screens bind the mouse wheel globally; remove it so it cannot
    # fire on a destroyed canvas after logout.
    for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
        root.unbind_all(sequence)

    for widget in root.winfo_children():
        widget.destroy()