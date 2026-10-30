import tkinter as tk

from ui import clear_window
import navigate


class BaseWelcomeScreen:
    def __init__(self, root, email, role_name):
        self.root = root
        self.email = email
        self.role_name = role_name
        self.username = email.split('@')[0]

        clear_window(self.root)

        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.setup_nav_bar()
        self.setup_scrollable_right_area()

    def setup_nav_bar(self):
        self.nav_bar = tk.Frame(self.main_container, bg="#2c3e50", width=200)
        self.nav_bar.pack(side=tk.LEFT, fill=tk.Y)
        self.nav_bar.pack_propagate(False)

        tk.Label(self.nav_bar, text="Rihla Portal", bg="#2c3e50", fg="white", font=("Arial", 16, "bold")).pack(pady=(20, 5))
        tk.Label(self.nav_bar, text=f"[{self.role_name}]", bg="#2c3e50", fg="#3498db", font=("Arial", 10, "italic")).pack(pady=(0, 20))

        self.add_nav_button("Dashboard")
        self.add_nav_button("Settings")

        tk.Button(self.nav_bar, text="Log Out", width=15, relief="raised", bg="#e74c3c", fg="white",
                  command=lambda: navigate.show_login(self.root)).pack(side=tk.BOTTOM, pady=20)

    def add_nav_button(self, text, command=None):
        btn = tk.Button(self.nav_bar, text=text, width=15, relief="flat", bg="#34495e", fg="white", command=command)
        btn.pack(pady=5)
        return btn

    def setup_scrollable_right_area(self):
        right_container = tk.Frame(self.main_container, bg="#ecf0f1")
        right_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(right_container, bg="#ecf0f1", highlightthickness=0)
        scrollbar = tk.Scrollbar(right_container, orient="vertical", command=self.canvas.yview)

        self.scrollable_frame = tk.Frame(self.canvas, bg="#ecf0f1")
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self._frame_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        # Make the content as wide as the visible area, so cards and tables fill the page.
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._frame_window, width=e.width))
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind mouse wheel events safely
        self.canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind_all("<Button-4>", self._on_mouse_wheel)
        self.canvas.bind_all("<Button-5>", self._on_mouse_wheel)

        # Unbind when canvas is destroyed to prevent background errors
        self.canvas.bind("<Destroy>", self._on_destroy)

        tk.Label(self.scrollable_frame, text=f"Welcome back, {self.username}!",
                 font=("Arial", 22, "bold"), bg="#ecf0f1", fg="#2c3e50").pack(anchor="w", padx=30, pady=(20, 5))

    def _on_mouse_wheel(self, event):
        try:
            if event.delta:
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")
        except Exception:
            pass

    def _on_destroy(self, event):
        try:
            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
        except Exception:
            pass