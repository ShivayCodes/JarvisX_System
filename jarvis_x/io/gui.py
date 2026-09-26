"""GUI interface for JARVIS-X using Tkinter."""
import tkinter as tk
from tkinter import scrolledtext, messagebox


class JarvisGUI:
    """Graphical user interface for JARVIS-X."""

    def __init__(self, engine):
        """
        Initialize the GUI.
        
        Args:
            engine: JarvisEngine instance.
        """
        self.engine = engine
        self.root = tk.Tk()
        self.root.title("JARVIS-X v7.0 - Local AI Assistant")
        self.root.geometry("800x600")
        self._setup_ui()

    def _setup_ui(self):
        """Set up the GUI components."""
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, state=tk.DISABLED,
            font=("Arial", 10), bg="#f0f0f0"
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Input frame
        input_frame = tk.Frame(self.root)
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        # Input field
        self.input_field = tk.Entry(input_frame, font=("Arial", 10))
        self.input_field.pack(fill=tk.X, side=tk.LEFT, expand=True)
        self.input_field.bind("<Return>", self._on_send)

        # Send button
        send_button = tk.Button(
            input_frame, text="Send", command=self._on_send,
            font=("Arial", 10), bg="#4CAF50", fg="white"
        )
        send_button.pack(side=tk.LEFT, padx=(10, 0))

        # Initial message
        self._display_message("JARVIS", "Hello! I'm JARVIS-X. How can I help you today?")

    def _on_send(self, event=None):
        """Handle send button click or Enter key."""
        user_input = self.input_field.get().strip()
        if not user_input:
            return

        # Display user message
        self._display_message("You", user_input)
        self.input_field.delete(0, tk.END)

        # Process query
        try:
            response = self.engine.process(user_input)
            self._display_message("JARVIS", response)
        except Exception as e:
            self._display_message("Error", str(e))

    def _display_message(self, sender: str, message: str):
        """Display a message in the chat."""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def run(self):
        """Run the GUI."""
        self.root.mainloop()
