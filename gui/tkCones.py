import os
import threading
import tkinter as tk
from tkinter import ttk

from gui.shell import log_shell

INPUT_PATH = "./input"


class ConesTab(ttk.Frame):
    def __init__(self, master, design=None, inputs_list=None, outputs_list=None):
        super().__init__(master, padding=10)
        self.design = design
        self.inputs_list = inputs_list or []
        self.outputs_list = outputs_list or []
        self.dot_file = f"{INPUT_PATH}/{design}.dot" if design else None
        self.json_cones = f"{INPUT_PATH}/cones_{design}.json" if design else None
        self._mounter = None  # Mount_cones, criado só no primeiro uso

        # Esquerda: seleção de output | Direita: botão
        ttk.Label(self, text="Output:").grid(row=0, column=0, padx=(0, 5), sticky="w")

        self.output_var = tk.StringVar(value=self.outputs_list[0] if self.outputs_list else "")
        self.output_combo = ttk.Combobox(
            self, textvariable=self.output_var,
            values=self.outputs_list, state="readonly", width=30,
        )
        self.output_combo.grid(row=0, column=1)

        self.btn_viewer = ttk.Button(self, text="Viewer Cones", command=self.view_cones)
        self.btn_viewer.grid(row=0, column=2, padx=(20, 0))

        self._check_inputs()

    def _check_inputs(self):
        """Avisa no terminal se faltar algo para o plot dos cones."""
        if not self.design:
            log_shell("Cones: nenhum design informado.", "warn")
            return
        if not self.outputs_list:
            log_shell("Cones: nenhum output encontrado no design.", "warn")
            return
        for path in (self.dot_file, self.json_cones):
            if not os.path.exists(path):
                log_shell(f"Cones: arquivo não encontrado: {path}", "error")
                return
        log_shell(f"Cones: {len(self.outputs_list)} outputs disponíveis.", "ok")

    def view_cones(self):
        output = self.output_var.get()
        if not output:
            log_shell("Cones: selecione um output primeiro.", "warn")
            return

        for path in (self.dot_file, self.json_cones):
            if not path or not os.path.exists(path):
                log_shell(f"Cones: arquivo não encontrado: {path}", "error")
                return

        self.btn_viewer.configure(state="disabled")
        log_shell(f"Cones: montando o cone de {output}...")
        threading.Thread(target=self._work, args=(output,), daemon=True).start()

    def _work(self, output):
        """Monta o .dot filtrado e abre no xdot, sem travar a interface."""
        dot_filtered = None
        try:
            from make_dots import filterCones
            if self._mounter is None:
                self._mounter = filterCones.Mount_cones(
                    self.inputs_list, self.dot_file, self.json_cones
                )
            dot_filtered = self._mounter.make_dot(output)
        except ImportError as e:
            log_shell(f"Cones: não consegui importar o filterCones: {e}", "error")
        except Exception as e:
            log_shell(f"Cones: erro ao montar o cone de {output}: {e}", "error")
        finally:
            # libera o botão já aqui: o xdot pode ficar aberto por muito tempo
            self.after(0, lambda: self.btn_viewer.configure(state="normal"))

        if dot_filtered is None:
            return

        log_shell(f"Cones: cone de {output} gerado em {dot_filtered}", "ok")
        try:
            from run.xdot import plot_graf
            plot_graf("", dot_filtered)
        except Exception as e:
            log_shell(f"Cones: erro ao abrir o grafo: {e}", "error")