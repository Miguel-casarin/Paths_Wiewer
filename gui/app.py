import threading
import tkinter as tk
from tkinter import ttk

from gui.shell import return_que_shell, log_shell
from gui.terminal import Terminal, redirect_stdout


class App(tk.Tk):
    def __init__(self, on_run=None):
        super().__init__()
        self.title("Gate Sizing")
        self.geometry("1000x650")
        self.on_run = on_run

        barra = ttk.Frame(self)
        barra.pack(fill="x", padx=8, pady=8)

        self.btn_rodar = ttk.Button(barra, text="Rodar", command=self.rodar)
        self.btn_rodar.pack(side="left")
        ttk.Button(barra, text="Limpar", command=lambda: self.terminal.limpar()).pack(side="left", padx=6)

        self.terminal = Terminal(self, return_que_shell())
        self.terminal.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        redirect_stdout()
        log_shell("Aplicação iniciada.", "ok")

    def rodar(self):
        if self.on_run is None:
            log_shell("Nenhuma função configurada.", "warn")
            return
        self.btn_rodar.configure(state="disabled")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        try:
            self.on_run()
        except Exception as e:
            log_shell(f"Erro: {e}", "error")
        finally:
            self.after(0, lambda: self.btn_rodar.configure(state="normal"))