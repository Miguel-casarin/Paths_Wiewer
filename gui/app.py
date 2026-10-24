import threading
import tkinter as tk
from tkinter import ttk

from gui.shell import return_que_shell, log_shell
from gui.terminal import Terminal, redirect_stdout
from gui.tkFeatures import FeaturesTab
from gui.tkCones import ConesTab
from gui.tkPaths import PathsTab


class App(tk.Tk):
    def __init__(self, on_run=None, features_dict=None, size_process=None,
                 design=None, design_inputs=None, design_outputs=None):
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
        self.tab_cones = ConesTab(self.notebook, design, design_inputs, design_outputs)
        self.tab_paths = PathsTab(self.notebook, design)

        self.notebook.add(self.tab_features, text="Features")
        self.notebook.add(self.tab_cones, text="Cones")
        self.notebook.add(self.tab_paths, text="Paths")
        paned.add(self.notebook, weight=3)

        # ----- Terminal (fixo, compartilhado por todas as abas) -----
        bottom = ttk.Frame(paned)
        barra = ttk.Frame(bottom)
        barra.pack(fill="x", pady=(0, 4))

        # O botão Rodar só existe se uma função on_run for passada
        self.btn_rodar = None
        if on_run is not None:
            self.btn_rodar = ttk.Button(barra, text="Rodar", command=self.rodar)
            self.btn_rodar.pack(side="left", padx=(0, 6))
        ttk.Button(barra, text="Limpar", command=lambda: self.terminal.clear()).pack(side="left")

        self.terminal = Terminal(bottom, return_que_shell())
        self.terminal.pack(fill="both", expand=True)
        paned.add(bottom, weight=1)

        redirect_stdout()
        log_shell("Aplicação iniciada.", "ok")

    def rodar(self):
        self.btn_rodar.configure(state="disabled")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        try:
            self.on_run()
        except Exception as e:
            log_shell(f"Erro: {e}", "error")
        finally:
            self.after(0, lambda: self.btn_rodar.configure(state="normal"))