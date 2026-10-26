import pprint
import re
import tkinter as tk
from tkinter import ttk

from gui.shell import log_shell


def _natural_key(chave):
    """Ordem natural: 2 antes de 10, e U2 antes de U10. Numeros vem antes de textos."""
    texto = str(chave)
    return [
        (0, int(p), "") if p.isdigit() else (1, 0, p)
        for p in re.split(r"(\d+)", texto)
        if p != ""
    ]


def _sort_recursivo(obj):
    """Devolve uma copia ordenada por chave (inclusive dicionarios aninhados)."""
    if isinstance(obj, dict):
        return {
            k: _sort_recursivo(v)
            for k, v in sorted(obj.items(), key=lambda kv: _natural_key(kv[0]))
        }
    return obj


def _as_dict(obj):
    """Aceita um dict ou um objeto (ex.: Save_features) e devolve algo imprimivel, ordenado por chave."""
    d = obj if isinstance(obj, dict) else (vars(obj) if hasattr(obj, "__dict__") else obj)
    return _sort_recursivo(d)


class DictWindow(tk.Toplevel):
    """Janela com o conteudo bruto de um dicionario, com rolagem vertical e horizontal."""

    def __init__(self, master, title):
        super().__init__(master)
        self.title(title)
        self.geometry("700x500")

        self.text = tk.Text(
            self, state="disabled", wrap="none",
            bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 10),
        )
        vscroll = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        hscroll = ttk.Scrollbar(self, orient="horizontal", command=self.text.xview)
        self.text.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.text.grid(row=0, column=0, sticky="nsew")
        vscroll.grid(row=0, column=1, sticky="ns")
        hscroll.grid(row=1, column=0, sticky="ew")

    def show(self, data):
        content = pprint.pformat(_as_dict(data), sort_dicts=False, width=100)
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("end", content)
        self.text.configure(state="disabled")


class FeaturesTab(ttk.Frame):
    """Tela principal (abre junto com o programa)."""

    def __init__(self, master, features_dict=None, size_process=None):
        super().__init__(master, padding=10)
        self.features_dict = features_dict
        self.size_process = size_process
        self._windows = {}  # titulo -> janela aberta (evita abrir duplicada)

        barra = ttk.Frame(self)
        barra.pack(anchor="nw")
        ttk.Button(barra, text="Show features", command=self.show_features).pack(side="left")
        ttk.Button(barra, text="Show steps", command=self.show_steps).pack(side="left", padx=6)

    def show_features(self):
        self._open("Features", self.features_dict)

    def show_steps(self):
        self._open("Steps", self.size_process)

    def _open(self, title, data):
        if data is None:
            log_shell(f"{title}: nenhum dado disponivel.", "warn")
            return

        win = self._windows.get(title)
        if win is None or not win.winfo_exists():
            win = DictWindow(self, title)
            self._windows[title] = win

        win.show(data)  # le o dicionario no momento do clique (sempre atualizado)
        win.lift()
        win.focus_set()