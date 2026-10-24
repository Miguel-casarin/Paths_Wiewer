import threading
import tkinter as tk
from tkinter import ttk

from gui.shell import return_que_shell, log_shell
from gui.terminal import Terminal, redirect_stdout
from gui.tkFeatures import FeaturesTab
from gui.tkCones import ConesTab
from gui.tkPaths import PathsTab


class App(tk.Tk):
    def __init__(self, on_run=None, features_dict=None, size_process=None):
        super().__init__()
        self.title("Gate Sizing")
        self.geometry("1000x700")
        self.on_run = on_run

        # Divisão vertical: abas em cima, terminal embaixo (redimensionável)
        paned = ttk.PanedWindow(self, orient="vertical")
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        # ----- Abas (a primeira, Features, abre com o programa) -----
        self.notebook = ttk.Notebook(paned)
        self.tab_features = FeaturesTab(self.notebook, features_dict, size_process)
        self.tab_cones = ConesTab(self.notebook)
        self.tab_paths = PathsTab(self.notebook)

        self.notebook.add(self.tab_features, text="Features")
        self.notebook.add(self.tab_cones, text="Cones")
        self.notebook.add(self.tab_paths, text="Paths")
        paned.add(self.notebook, weight=3)

        # ----- Terminal (fixo, compartilhado por todas as abas) -----
        bottom = ttk.Frame(paned)
        barra = ttk.Frame(bottom)
        barra.pack(fill="x", pady=(0, 4))

        ttk.Label(barra, text="Design:").pack(side="left")
        self.design_var = tk.StringVar()
        entry = ttk.Entry(barra, textvariable=self.design_var, width=20)
        entry.pack(side="left", padx=(4, 8))
        entry.bind("<Return>", lambda e: self.rodar())

        self.btn_rodar = ttk.Button(barra, text="Rodar", command=self.rodar)
        self.btn_rodar.pack(side="left")
        ttk.Button(barra, text="Limpar", command=lambda: self.terminal.clear()).pack(side="left", padx=6)

        self.terminal = Terminal(bottom, return_que_shell())
        self.terminal.pack(fill="both", expand=True)
        paned.add(bottom, weight=1)

        redirect_stdout()
        log_shell("Aplicação iniciada.", "ok")

    def rodar(self):
        if self.on_run is None:
            log_shell("Nenhuma função configurada.", "warn")
            return
        self.btn_rodar.configure(state="disabled")
        design = self.design_var.get()  # lido aqui, na thread da interface
        threading.Thread(target=self._worker, args=(design,), daemon=True).start()

    def _worker(self, design):
        try:
            self.on_run(design)
        except Exception as e:
            log_shell(f"Erro: {e}", "error")
        finally:
            self.after(0, lambda: self.btn_rodar.configure(state="normal"))