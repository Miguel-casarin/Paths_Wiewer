import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import readVerilog, readSTA, editTCL
from run import runSTA
from utils import divide, files


class Size_order:
    """Dimensiona, uma por vez, as células do circuito e devolve, para cada step,
    a diferença de arrival (starter - step), caminho por caminho.

    Usa o priority.tcl, que desfaz cada troca no fim do step (não acumula).
    Os TCLs são montados e rodados em paralelo, igual ao fluxo do main.py.
    """

    def __init__(self, design, starter_arrivals, cells=None,
                 verilogs="./verilogs", library="Nangate45_typ.lib",
                 library_path="./library", tcl_template="./tcl/priority.tcl",
                 temp_path="./temp", max_workers=None):
        """
        starter_arrivals: {path_id: arrival} do circuito sem dimensionar
                          (Read_sta(...).get_arrival_times() do starter).
        cells: células a testar, na ordem dos steps (step N = cells[N-1]).
               Se None, usa todas as células do Verilog.
        """
        self.design = design[:-2] if design.endswith(".v") else design
        self.starter_arrivals = starter_arrivals
        self.verilog_path = f"{verilogs}/{self.design}.v"
        self.lib_path = f"{library_path}/{library}"
        self.tcl_template = tcl_template
        self.temp_path = temp_path
        self.max_workers = max_workers or max(1, (os.cpu_count() or 2) - 1)
        self.failed = []  # TCLs que deram erro na última execução

        # inputs, outputs e módulo do circuito
        design_io = readVerilog.Get_IO(self.verilog_path)
        self.module = design_io.verilog_module()
        self.inputs = design_io.get_inputs()
        self.outputs = design_io.get_outputs()

        if cells is None:
            cells = readVerilog.Gates_info(self.verilog_path).get_cells_ids()
        self.cells = list(cells)
        if not self.cells:
            raise ValueError("Nenhuma célula para dimensionar")

    # ---------------------------------------------------------------- TCLs
    def make_tcls(self) -> list:
        """Divide as células entre as threads e gera um TCL por fatia."""
        works_number = divide.define_threads(self.max_workers, self.cells)
        works_indexs = divide.particion_list(self.cells, works_number)
        steps_starter = divide.starter_steps(works_number, self.cells)

        os.makedirs(self.temp_path, exist_ok=True)
        step_tcls = []
        for step, (start, end) in zip(steps_starter, works_indexs):
            # nome próprio, para não sobrescrever os step{N}_{design}.tcl do main.py
            name = f"priority{step}_{self.design}.tcl"
            files.copy_rename(self.tcl_template, name, self.temp_path)
            tcl = f"{self.temp_path}/{name}"

            # o priority.tcl não tem pre_sized_list (nada acumula), então usa o setup_size_tcl
            editTCL.setup_size_tcl(
                tcl,
                verilog_path=self.verilog_path,
                module_name=self.module,
                inputs_list=self.inputs,
                outputs_list=self.outputs,
                cells_list=self.cells[start:end],
                step=step,
                lib_path=self.lib_path,
            )
            step_tcls.append(tcl)
        return step_tcls

    # ------------------------------------------------------------ execução
    def run(self) -> dict:
        """Roda todos os TCLs em paralelo e retorna {step: {path_id: starter - step}}."""
        step_tcls = self.make_tcls()
        print(f"[Size_order] {len(self.cells)} células, {len(step_tcls)} TCLs, "
              f"{self.max_workers} threads")

        differences = {}
        self.failed = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {pool.submit(self._run_tcl, tcl): tcl for tcl in step_tcls}
            for future in as_completed(futures):
                tcl = futures[future]
                try:
                    differences.update(future.result())
                except Exception as error:
                    self.failed.append(tcl)
                    print(f"[ERROR] Size_order {tcl}:\n{error}")

        return dict(sorted(differences.items()))

    def _run_tcl(self, tcl: str) -> dict:
        """Roda um TCL no OpenSTA e devolve {step: diferença} dos steps dele."""
        output = runSTA.run_sta(tcl)
        steps = readSTA.Read_steps(output).get_arrival_times()
        if not steps:
            raise ValueError(f"Nenhum 'STEP: N' encontrado na saída de {tcl}")
        return {step: self._difference(arrivals) for step, arrivals in steps.items()}

    def _difference(self, step_arrivals: dict) -> dict:
        """starter - step, arrival por arrival (mesmo path_id).
        Caminhos que não existem nos dois lados são ignorados."""
        return {
            path_id: round(self.starter_arrivals[path_id] - value, 5)
            for path_id, value in step_arrivals.items()
            if path_id in self.starter_arrivals
        }

    # ------------------------------------------------------- arquivo de prioridade
    def save_priority(self, differences: dict, save_dir="./input", reverse=False) -> str:
        """Salva {save_dir}/{design}_priority.txt, uma célula por linha, no mesmo
        formato do c432_priority.txt.

        A nota de cada célula é a soma das diferenças (starter - step) de todos os
        caminhos do step dela. Ordem: da menor para a maior nota (reverse=True inverte).
        Células com mesma nota mantêm a ordem dos steps.
        """
        if not differences:
            raise ValueError("Sem diferenças para ordenar (todos os TCLs falharam?)")

        # step N corresponde a self.cells[N-1]
        scores = {
            self.cells[step - 1]: round(sum(diff.values()), 5)
            for step, diff in differences.items()
        }

        missing = [cell for cell in self.cells if cell not in scores]
        if missing:
            print(f"[WARN] Size_order: {len(missing)} células sem resultado "
                  f"(ficam fora do arquivo): {missing}")

        ordered = sorted(scores, key=scores.get, reverse=reverse)

        os.makedirs(save_dir, exist_ok=True)
        path = f"{save_dir}/{self.design}_priority.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(ordered) + "\n")

        print(f"[Size_order] prioridade salva em {path} ({len(ordered)} células)")
        return path