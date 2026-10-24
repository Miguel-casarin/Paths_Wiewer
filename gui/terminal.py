import queue
import sys
import tkinter as tk
from tkinter import ttk

from gui.shell import log_shell


class Terminal(ttk.Frame):
    def __init__(self, master, que_shell, interval_ms=50, max_lines=5000):
        super().__init__(master)
        self.que_shell = que_shell
        self.interval_ms = interval_ms
        self.max_lines = max_lines

        self.text = tk.Text(
            self, state="disabled", wrap="word",
            bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 10),
        )
        scroll = ttk.Scrollbar(self, command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        self.text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.text.tag_configure("info", foreground="#d4d4d4")
        self.text.tag_configure("ok", foreground="#6a9955")
        self.text.tag_configure("warn", foreground="#dcdcaa")
        self.text.tag_configure("error", foreground="#f44747")

        self.after(self.interval_ms, self._consume_queue)

    def _consume_queue(self):
        try:
            while True:
                level, msg = self.que_shell.get_nowait()
                self._write(msg, level)
        except queue.Empty:
            pass
        self.after(self.interval_ms, self._consume_queue)

    def _write(self, msg, level):
        self.text.configure(state="normal")
        self.text.insert("end", msg + "\n", level)
        lines = int(self.text.index("end-1c").split(".")[0])
        if lines > self.max_lines:
            self.text.delete("1.0", f"{lines - self.max_lines}.0")
        self.text.configure(state="disabled")
        self.text.see("end")

    def clear(self):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")


class Queue_Writer:
    """Makes print() and stderr go to the GUI terminal."""
    def __init__(self, level="info"):
        self.level = level

    def write(self, s):
        if s.strip():
            log_shell(s.rstrip("\n"), self.level)

    def flush(self):
        pass


def redirect_stdout():
    sys.stdout = Queue_Writer("info")
    sys.stderr = Queue_Writer("error")