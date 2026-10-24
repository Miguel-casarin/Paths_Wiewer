import difflib
import os
import re
import threading
import tkinter as tk
from tkinter import ttk

from gui.shell import log_shell
from make_dots.readPathsSteps import Search_steps
from make_dots.SubPaths import DotSubgraph

INPUT_PATH = "./input"
TEMP_PATH = "./temp"

_SUFFIX_RE = re.compile(r"[v^]$")


def _split_path(path: str) -> list:
    return [n.strip() for n in path.split("->")]


def _gate_name(node: str) -> str:
    """Nome do gate sem a transição final (^ ou v). Ex.: '_146_^' -> '_146_'."""
    return _SUFFIX_RE.sub("", node.strip())


# retorna as rotas que mudaram comparando as strings inteiras dos arrivals
def show_dif(previous_step: dict, current_step: dict) -> dict:
    changed = {}

    for key, curr_path in current_step.items():
        prev_path = previous_step.get(key)
        if curr_path != prev_path:
            changed[key] = {"prev": prev_path, "curr": curr_path}

    # arrivals que existiam no anterior e sumiram no atual
    for key, prev_path in previous_step.items():
        if key not in current_step:
            changed[key] = {"prev": prev_path, "curr": None}

    return changed


# retorna todos os steps em que ocorreu mudanças
def steps_changes(search_obj, steps: list) -> list:
    changed_steps = []
    prev_data = search_obj.arrivals_by_step(steps[0]) if steps else {}
    for curr_num in steps[1:]:
        curr_data = search_obj.arrivals_by_step(curr_num)
        if show_dif(prev_data, curr_data):
            changed_steps.append(curr_num)
        prev_data = curr_data  # reaproveita: evita ler o mesmo step duas vezes
    return changed_steps


class PathsTab(ttk.Frame):
    def __init__(self, master, design=None):
        super().__init__(master, padding=10)
        self.design = design
        self.dot_file = f"{INPUT_PATH}/{design}.dot" if design else None
        self.steps_file = f"{INPUT_PATH}/{design}_cumulativo.txt" if design else None

        self.search_obj = None
        self.steps = []
        self.current_dif = {}
        self._subgraph = None  # DotSubgraph, criado só quando necessário

        # Coluna 0 (lista) expande, coluna 1 (botões) fixa
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # ----- Lado esquerdo: lista + scrollbar -----
        left = ttk.Frame(self)
        left.grid(row=0, column=0, sticky="nsew")
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)

        self.listbox = tk.Listbox(left, selectmode=tk.SINGLE, exportselection=False)
        scrollbar = ttk.Scrollbar(left, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        self.listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.listbox.bind("<Double-Button-1>", lambda e: self.view_paths())

        # ----- Lado direito: status e botões -----
        right = ttk.Frame(self, padding=(10, 0, 0, 0))
        right.grid(row=0, column=1, sticky="n")

        self.status_var = tk.StringVar(value="Select a step")
        ttk.Label(right, textvariable=self.status_var).pack(pady=(0, 10))

        for text, command in (
            ("Show Differences", self.open_dif_window),
            ("Summary of Changes", self.open_all_changes_window),
            ("View Paths", self.view_paths),
            ("Path on Circuit", self.path_on_circuit),
            ("View Step Content", self.open_step_window),
        ):
            ttk.Button(right, text=text, command=command).pack(pady=(0, 10))

        self.load()

    # ------------------------------------------------------------------ dados
    def load(self):
        """Lê a lista de steps do arquivo cumulativo e preenche a lista."""
        self.listbox.delete(0, tk.END)
        self.steps = []
        self.current_dif = {}
        self._subgraph = None
        self.status_var.set("Select a step")

        if not self.design:
            log_shell("Paths: nenhum design informado.", "warn")
            return

        self.search_obj = Search_steps(self.dot_file, self.steps_file)
        try:
            self.steps = self.search_obj.count_steps()
        except FileNotFoundError:
            log_shell(f"Paths: arquivo não encontrado: {self.steps_file}", "error")
            return

        if not self.steps:
            log_shell("Paths: nenhum step encontrado no arquivo.", "warn")
            return

        for step in self.steps:
            self.listbox.insert(tk.END, f"Step {step}")
        log_shell(f"Paths: {len(self.steps)} steps carregados.", "ok")

    def _get_subgraph(self) -> DotSubgraph:
        if self._subgraph is None:
            self._subgraph = DotSubgraph(self.dot_file)
        return self._subgraph

    def _selected_step(self):
        """Step selecionado, ou None (com aviso no terminal)."""
        selection = self.listbox.curselection()
        if not selection:
            log_shell("Selecione um step primeiro.", "warn")
            return None
        return self.steps[selection[0]]

    # ----------------------------------------------------------------- eventos
    def on_select(self, event):
        selection = self.listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        step = self.steps[idx]

        if idx == 0:
            self.status_var.set(f"Step {step} (Base) - No previous step")
            self.current_dif = {}
            return

        prev_data = self.search_obj.arrivals_by_step(self.steps[idx - 1])
        curr_data = self.search_obj.arrivals_by_step(step)
        self.current_dif = show_dif(prev_data, curr_data)

        self.status_var.set(f"Step {step}: " + ("Changed" if self.current_dif else "No change"))

    # ---------------------------------------------------------------- janelas
    def _text_window(self, title, geometry, wrap=tk.WORD):
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry(geometry)

        frame = ttk.Frame(win, padding=10)
        frame.pack(expand=True, fill=tk.BOTH)
        scroll = ttk.Scrollbar(frame, orient="vertical")
        text = tk.Text(frame, wrap=wrap, yscrollcommand=scroll.set)
        scroll.config(command=text.yview)
        text.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        return text

    def open_dif_window(self):
        text = self._text_window("Differences Found", "600x400")
        text.tag_config("red", foreground="red")

        if not self.current_dif:
            text.insert(tk.END, "No route differences found in this step compared to the previous step.\n")
        else:
            for arr_key, changes in self.current_dif.items():
                prev_path, curr_path = changes["prev"], changes["curr"]
                text.insert(tk.END, f"{arr_key}:\n")
                text.insert(tk.END, f"  Previous: {prev_path or '(Did not exist)'}\n")
                if curr_path:
                    self._insert_current(text, prev_path, curr_path)
                else:
                    text.insert(tk.END, "  Current:  (Removed)\n")
                text.insert(tk.END, "\n")

        text.config(state=tk.DISABLED)  # somente leitura

    @staticmethod
    def _insert_current(text, prev_path, curr_path):
        """Escreve a rota atual, em vermelho os gates que não existiam na anterior."""
        text.insert(tk.END, "  Current:  ")
        if not prev_path:
            text.insert(tk.END, f"{curr_path}\n", "red")
            return

        curr_nodes = _split_path(curr_path)
        prev_gates = [_gate_name(n) for n in _split_path(prev_path)]
        curr_gates = [_gate_name(n) for n in curr_nodes]

        # compara só o nome do gate, ignorando a transição (^ ou v)
        red = set()
        matcher = difflib.SequenceMatcher(None, prev_gates, curr_gates)
        for tag, _, _, j1, j2 in matcher.get_opcodes():
            if tag in ("replace", "insert"):
                red.update(range(j1, j2))

        for idx, node in enumerate(curr_nodes):
            if idx in red:
                text.insert(tk.END, node, "red")
            else:
                text.insert(tk.END, node)
            if idx < len(curr_nodes) - 1:
                text.insert(tk.END, " -> ")
        text.insert(tk.END, "\n")

    def open_all_changes_window(self):
        log_shell("Paths: calculando steps com mudanças...")

        def work():
            try:
                changed = steps_changes(self.search_obj, self.steps)
            except Exception as e:
                log_shell(f"Paths: erro ao calcular mudanças: {e}", "error")
                return
            self.after(0, lambda: self._show_changes(changed))

        threading.Thread(target=work, daemon=True).start()

    def _show_changes(self, changed):
        log_shell(f"Paths: {len(changed)} steps com mudanças.", "ok")
        text = self._text_window("Steps with Changes", "250x300")
        if not changed:
            text.insert(tk.END, "No step showed any changes.\n")
        else:
            for step in changed:
                text.insert(tk.END, f"Step {step}\n")
        text.config(state=tk.DISABLED)

    def open_step_window(self):
        step = self._selected_step()
        if step is None:
            return

        try:
            content = self.search_obj.return_step(step)
        except Exception as e:
            log_shell(f"Paths: erro ao ler o step {step}: {e}", "error")
            return

        text = self._text_window(f"Step {step} Details", "500x400")
        text.insert(tk.END, content)
        text.config(state=tk.DISABLED)

    # ------------------------------------------------------------------ grafos
    def view_paths(self):
        """Gera e abre o subgrafo com as rotas que mudaram no step selecionado."""
        step = self._selected_step()
        if step is None:
            return

        if not self.current_dif:
            log_shell(f"Step {step}: sem mudanças, nada para gerar.", "info")
            return

        # todos os gates das rotas atuais que sofreram mudança
        gates = set()
        for changes in self.current_dif.values():
            if changes["curr"]:
                gates.update(_gate_name(n) for n in _split_path(changes["curr"]))

        if not gates:
            log_shell(f"Step {step}: nenhum gate encontrado nas rotas.", "info")
            return

        os.makedirs(TEMP_PATH, exist_ok=True)
        out_dot = f"{TEMP_PATH}/{step}_{self.design}_paths.dot"
        try:
            self._get_subgraph().generate(gates, out_dot)
        except Exception as e:
            log_shell(f"Paths: erro ao gerar o grafo: {e}", "error")
            return

        log_shell(f"Step {step}: subgrafo gerado em {out_dot}", "ok")
        self._plot(out_dot)

    def path_on_circuit(self):
        """Abre o circuito inteiro com as rotas do step selecionado em vermelho."""
        step = self._selected_step()
        if step is None:
            return

        paths_dict = self.search_obj.arrivals_by_step(step)
        if not paths_dict:
            log_shell(f"Step {step}: nenhum arrival encontrado.", "info")
            return

        try:
            out_dot = self._circuit_with_paths(step, paths_dict)
        except Exception as e:
            log_shell(f"Paths: erro ao gerar o circuito com paths: {e}", "error")
            return

        log_shell(f"Step {step}: circuito gerado em {out_dot}", "ok")
        self._plot(out_dot)

    def _circuit_with_paths(self, step: int, paths_dict: dict) -> str:
        """Copia o .dot do circuito pintando de vermelho as arestas dos paths."""
        os.makedirs(TEMP_PATH, exist_ok=True)
        out_dot = f"{TEMP_PATH}/{step}_{self.design}_circuit.dot"
        gate_to_node = self._get_subgraph().gate_to_node

        pairs_to_color = set()
        for path_str in paths_dict.values():
            if not path_str:
                continue
            gates = [_gate_name(n) for n in _split_path(path_str) if n]
            for u_name, v_name in zip(gates, gates[1:]):
                u_id, v_id = gate_to_node.get(u_name), gate_to_node.get(v_name)
                if u_id and v_id:
                    pairs_to_color.add((u_id, v_id))

        with open(self.dot_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            edge = DotSubgraph.EDGE_RE.match(line)
            if edge:
                src = edge.group(1).split(":")[0]
                tgt = edge.group(2).split(":")[0]
                if (src, tgt) in pairs_to_color:
                    line_mod, count = re.subn(r'(?<!font)color="[^"]*"', 'color="red"', line)
                    if count == 0:
                        line_mod = line.replace("[", '[color="red", ', 1)
                    new_lines.append(line_mod)
                    continue
            new_lines.append(line)

        with open(out_dot, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return out_dot

    def _plot(self, dot_path: str):
        """Abre o .dot no xdot sem travar a interface; erros vão para o terminal."""
        def work():
            try:
                from run.xdot import plot_graf
                plot_graf("", dot_path)
            except Exception as e:
                log_shell(f"Paths: erro ao abrir o grafo: {e}", "error")

        threading.Thread(target=work, daemon=True).start()