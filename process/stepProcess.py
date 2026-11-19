import os
import sys

from . import editTCL, readSTA
from make_dots import editDot, arrivals
from utils import files, colorsMake
from run import runSTA

VERILOGS = "./verilogs"
LIBRARY = "Nangate45_typ.lib"
LIBRARY_PATH = "./library"
TCL_PATH = "./tcl"
TEMP_PATH = "./temp"
OUT_PATH = "./out"
INPUT_PATH = "./input"


class Step_content:
    def __init__(self, design: str, upsized_cells: list, step: int = 0):
        self.design = design
        self.upsized_cells = upsized_cells
        self.step = step

    def build_step_dot(self, step: int) -> str:
        """Gera sob demanda o .dot do step usando upsized_cells e retorna o caminho."""
        base_dot = f"{INPUT_PATH}/{self.design}.dot"
        step_name = f"step{step}_{self.design}.dot"
        step_dot = f"{TEMP_PATH}/{step_name}"

        if os.path.isfile(step_dot):
            return step_dot

        files.copy_rename(base_dot, step_name, TEMP_PATH)

        if step > 0:
            sized_cells = self.upsized_cells[:step]
            if sized_cells:
                with open(step_dot, "r", encoding="utf-8") as f:
                    editor = editDot.Edit_Dot(f.read())
                editor.upsize_cells(sized_cells)
                with open(step_dot, "w", encoding="utf-8") as f:
                    f.write(editor.dot_file)

        return step_dot

    def edit_step_sta(self, sta_file: str, verilog: str, module: str, inputs_list: list, outputs_list: list, sized_cells: list = None, total_paths: int = None):
        if total_paths is None:
            total_paths = len(outputs_list)

        try:
            editTCL.edit_verilog(sta_file, verilog)
            editTCL.edit_link_design(sta_file, module)
            editTCL.parse_inputs(sta_file, inputs_list)
            editTCL.parse_outputs(sta_file, outputs_list)
            editTCL.paths_total(sta_file, total_paths)
        except Exception as error:
            print(f"ERROR TO EDIT TCL FILE: \n{error}")
            sys.exit(1)

        
        
    def read_pathas(self, sta_file: str, verilog: str, module: str, inputs_list: list, outputs_list: list, sized_cells: list = None, total_paths: int = None) -> dict:
        if total_paths is None:
                    total_paths = len(outputs_list)
                    
        file = os.path.basename(sta_file)
        
        file_exites = files.file_exists("./temp", file)
        
        if file_exites:
            
            try:
                path_times = runSTA.run_sta(sta_file)
            except Exception as error:
                print(f"ERROR TO RUN OpenSTA : \n{error}")
                sys.exit(1)
            
            try:
                times = readSTA.Read_paths(path_times)
                dict_times = times.get_paths()
            except Exception as error:
                print(f"ERROR TO GET TIMES : \n{error}")
                sys.exit(1)
                
        else:
            
            self.edit_step_sta(sta_file, verilog, module, inputs_list, outputs_list, sized_cells, total_paths)
            
            try:
                path_times = runSTA.run_sta(sta_file)
            except Exception as error:
                print(f"ERROR TO RUN OpenSTA : \n{error}")
                sys.exit(1)
            
            try:
                times = readSTA.Read_paths(path_times)
                dict_times = times.get_paths()
            except Exception as error:
                print(f"ERROR TO GET TIMES : \n{error}")
                sys.exit(1)
                
        return dict_times

    def color_plot(self, dot_file: str, dict_values: dict, path_id: int):
        if path_id == 1:
            arrivals.paint_path(dot_file, dict_values, path_id, [255, 165, 0])
        else:
            color = colorsMake.color()
            arrivals.paint_path(dot_file, dict_values, path_id, color)
