# stops the timers, removes the mouse wheel bindings and destroys all the widgets
def clear_window(root):
    jobs = root.tk.splitlist(root.tk.call('after', 'info'))
    for job in jobs:
        root.after_cancel(job)

    # the welcome screens bind the mouse wheel on everything, remove it so it
    # doesnt fire on a canvas that is already destroyed after logout
    root.unbind_all("<MouseWheel>")
    root.unbind_all("<Button-4>")
    root.unbind_all("<Button-5>")

    for widget in root.winfo_children():
        widget.destroy()
