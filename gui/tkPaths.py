from tkinter import ttk


class PathsTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        ttk.Label(self, text="Paths").pack(anchor="nw")
        # TODO: widgets da tela de Paths