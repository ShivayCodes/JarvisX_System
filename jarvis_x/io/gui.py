import threading
import importlib
import tkinter as tk
from tkinter import scrolledtext

from jarvis_x.core.config import Config, IS_WINDOWS


class JarvisGUI:
    def __init__(self, engine):
        self.engine = engine
        self.root = None
        self.chat_display = None
        self.input_field = None
        self.tray_icon = None
        self._has_tray = False
        self._setup()

    def _setup(self):
        self.root = tk.Tk()
        self.root.title(Config.GUI_TITLE)
        self.root.geometry(f"{Config.GUI_WIDTH}x{Config.GUI_HEIGHT}")
        self.root.minsize(500, 400)

        if IS_WINDOWS:
            try:
                self.root.iconbitmap(default="")
            except Exception:
                pass

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        chat_frame = tk.Frame(self.root)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))

        self.chat_display = scrolledtext.ScrolledText(
            chat_frame, wrap=tk.WORD, font=("Consolas", 10),
            bg="#1e1e1e", fg="#d4d4d4", insertbackground="white",
            state=tk.DISABLED, relief=tk.FLAT, borderwidth=0
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        self.chat_display.tag_config("user", foreground="#569cd6", font=("Consolas", 10, "bold"))
        self.chat_display.tag_config("jarvis", foreground="#6a9955", font=("Consolas", 10, "bold"))
        self.chat_display.tag_config("system", foreground="#808080", font=("Consolas", 9))
        self.chat_display.tag_config("error", foreground="#f44747", font=("Consolas", 10, "bold"))

        input_frame = tk.Frame(self.root)
        input_frame.pack(fill=tk.X, padx=10, pady=(5, 10))

        self.input_field = tk.Entry(input_frame, font=("Consolas", 11),
                                     bg="#252526", fg="#d4d4d4",
                                     insertbackground="white", relief=tk.FLAT, borderwidth=2)
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)
        self.input_field.bind("<Return>", lambda e: self._send())

        send_btn = tk.Button(input_frame, text="Send", command=self._send,
                              bg="#0e639c", fg="white", relief=tk.FLAT,
                              padx=15, cursor="hand2")
        send_btn.pack(side=tk.RIGHT, padx=(5, 0))

        status_frame = tk.Frame(self.root, bg="#252526")
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = tk.Label(status_frame, text="Online", anchor=tk.W,
                                      bg="#252526", fg="#808080", font=("Consolas", 8))
        self.status_label.pack(fill=tk.X, padx=10, pady=2)

        try:
            importlib.import_module("pystray")
            importlib.import_module("PIL.Image")
            importlib.import_module("PIL.ImageDraw")
            self._has_tray = True
            self.root.protocol("WM_DELETE_WINDOW", self._minimize_to_tray)
            self.root.bind("<Unmap>", self._on_minimize)
        except ImportError:
            self._has_tray = False

        self._append("System", "JARVIS-X v7.0 ready. Type 'help' for commands.", "system")
        self.input_field.focus()

    def _append(self, sender: str, message: str, tag: str = "jarvis"):
        if not self.root:
            return
        try:
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, f"{sender}: ", tag)
            self.chat_display.insert(tk.END, f"{message}\n\n",
                                     "system" if sender == "System" else tag)
            self.chat_display.see(tk.END)
            self.chat_display.config(state=tk.DISABLED)
        except Exception:
            pass

    def _send(self):
        text = self.input_field.get().strip()
        if not text:
            return
        self.input_field.delete(0, tk.END)
        self._append("You", text, "user")
        self.root.update()
        try:
            response = self.engine.process_with_history(text)
            self._append("JARVIS", response)
            if not self.engine.running:
                self.root.after(500, self._on_close)
        except Exception as e:
            self._append("JARVIS", f"Error: {str(e)}", "error")

    def _create_tray_icon(self):
        try:
            Image = importlib.import_module("PIL.Image")
            ImageDraw = importlib.import_module("PIL.ImageDraw")
            pystray = importlib.import_module("pystray")
            img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.ellipse([8, 8, 56, 56], fill="#0e639c")
            draw.text((20, 18), "J", fill="white", font=None)
            menu = pystray.Menu(
                pystray.MenuItem("Show", self._show_window, default=True),
                pystray.MenuItem("Hide", self._minimize_to_tray),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", self._quit_app)
            )
            self.tray_icon = pystray.Icon(Config.APP_NAME, img, Config.GUI_TITLE, menu)
            self.tray_icon.run_detached()
        except ImportError:
            pass

    def _minimize_to_tray(self):
        if self.root:
            self.root.withdraw()
        if self._has_tray and not self.tray_icon:
            threading.Thread(target=self._create_tray_icon, daemon=True).start()

    def _show_window(self):
        if self.root:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None

    def _on_minimize(self, event):
        if self._has_tray and self.root and self.root.state() == "iconic":
            self._minimize_to_tray()

    def _on_close(self):
        self._quit_app()

    def _quit_app(self):
        if self.tray_icon:
            self.tray_icon.stop()
        self.engine.shutdown()
        if self.root:
            self.root.destroy()

    def run(self):
        self.root.mainloop()
