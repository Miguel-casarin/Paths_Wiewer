from concurrent.futures import ThreadPoolExecutor, as_completed

from process import editTCL
from process.FindPaths import previos_ocurence, curence_ocurence
from utils import files

# impact.py: ajuste aqui se ele estiver em outra pasta
try:
    from utils import impact
except ImportError:
    from process import impact


class Make_TCL_Steps:
    def __init__(self,
                 tcl_template: str,      # ./tcl/sizeParallel.tcl
                 verilog_path: str,
                 lib_path: str,
                 module: str,
                 inputs_list: list,
                 outputs_list: list,
                 cells_to_upsize: list,
                 design: str,
                 temp_path: str = "./temp"):
        self.template = tcl_template
        self.verilog = verilog_path
        self.lib = lib_path
        self.module = module
        self.inputs = inputs_list
        self.outputs = outputs_list
        self.cells = cells_to_upsize
        self.design = design
        self.temp_path = temp_path

    def build(self, step: int, start: int, end: int) -> str:
        """Gera temp/step<step>_<design>.tcl para o worker que cobre
        cells[start:end]. Retorna o caminho do arquivo."""
        name = f"step{step}_{self.design}.tcl"
        files.copy_rename(self.template, name, self.temp_path)
        out = f"{self.temp_path}/{name}"

        editTCL.setup_parallel_tcl(
            tcl_file=out,
            verilog_path=self.verilog,
            module_name=self.module,
            inputs_list=self.inputs,
            outputs_list=self.outputs,
            cells_list=self.cells[start:end],
            pre_sized_list=self.cells[:start],
            step=step,
            lib_path=self.lib,
        )
        return out


class Run_Steps:
    def __init__(self,
                 base_power: float,
                 base_arrivals: dict,
                 results: dict,          # SIZE_PROCESS
                 max_workers: int):
        self.base_power = base_power
        self.base_arrivals = base_arrivals
        self.results = results
        self.max_workers = max_workers

    def run(self, tcl_files: list) -> dict:
        workers = max(1, min(self.max_workers, len(tcl_files)))

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    impact.run_sta_impact_and_paths,
                    f, self.base_power, self.base_arrivals
                ): f
                for f in tcl_files
            }

            for future in as_completed(futures):
                tcl_name = futures[future]
                try:
                    steps_data, line_count = future.result()
                    self.results.update(steps_data)
                    print(f"[OK] {tcl_name} executado com sucesso! "
                          f"({line_count} linhas geradas)")
                except Exception as e:
                    print(f"[ERRO] {tcl_name} falhou: {e}")

        self._fill_occurrences()
        return self.results

    def _fill_occurrences(self):
        """Preenche 'previos' e 'curente' com a ocorrência da célula
        dimensionada no step anterior e no atual. Só roda depois que
        todos os TCLs terminaram."""
        for step in sorted(self.results):
            data = self.results[step]
            cell = data.get("cell")
            if cell is None:
                continue
            data["previos"] = previos_ocurence(self.results, step, cell)
            data["curente"] = curence_ocurence(self.results, step, cell)