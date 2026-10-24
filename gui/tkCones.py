from tkinter import ttk


class ConesTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        ttk.Label(self, text="Cones").pack(anchor="nw")
        # TODO: widgets da tela de Cones