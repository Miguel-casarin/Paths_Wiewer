import sys 
import pprint

from process import readVerilog, ReadNetlist, editTCL, readSTA
from make_dots import circuitDot, arrivals
from run import runSTA
from utils import files, colorsMake

while True:
    circuit = input("DESIGN TO RUN : ").strip()
    if not circuit.endswith(".v"):
        circuit += ".v"          # aceita "c17" ou "c17.v"
    if files.file_exists("verilogs", circuit):
        break
    print(f"File '{circuit}' not found in verilogs/. Try again.")

DESIGN = circuit[:-2]
VERILOGS = "./verilogs"
LIBRARY = "Nangate45_typ.lib"
LIBRARY_PATH = "./library"
TCL_PATH = "./tcl"
TEMP_PATH = "./temp"

# inputs, outputs, cells, logic types
try:
    design_io = readVerilog.Get_IO(f"{VERILOGS}/{DESIGN}.v")
    design_module = design_io.verilog_module()
    design_inputs = design_io.get_inputs()
    design_outputs = design_io.get_outputs()
except Exception as error:
    print(f"[ERROR] TO GET IO :\n{error}")
    sys.exit(1)

# edita o tcl

files.copy_rename(f"{TCL_PATH}/criticalPath.tcl", f"path_{DESIGN}.tcl", TEMP_PATH)
tcl = f"{TEMP_PATH}/path_{DESIGN}.tcl"

try:
    editTCL.edit_liberty(tcl, f"{LIBRARY_PATH}/{LIBRARY}")
    editTCL.edit_verilog(tcl, f"{VERILOGS}/{DESIGN}.v")
    editTCL.edit_link_design(tcl, design_module)
    editTCL.parse_inputs(tcl, design_inputs)
    editTCL.parse_outputs(tcl, design_outputs)
    editTCL.paths_total(tcl, len(design_outputs))
except Exception as error:
    print(f"[ERROR] TO EDIT BASE TCL :\n{error}")
    sys.exit(1)

try:
    path_times = runSTA.run_sta(tcl)
except Exception as error:
    print(f"ERROR TO RUN OpenSTA : \n{error}")
    sys.exit(1)

try:
    times = readSTA.Read_paths(path_times)
    dict_times = times.get_paths()
except Exception as error:
    print(f"ERROR TO GET TIMES : \n{error}")
    sys.exit(1)
    

# constrou o .dot básico
circuitDot.verilog_to_dot(f"{VERILOGS}/{DESIGN}.v", TEMP_PATH)

def color_plot(dot_file: str, dict_values: dict, path_id: int):
    if path_id == 1:
        arrivals.paint_path(dot_file, dict_values, path_id, [255, 165, 0])
    else:
        color = colorsMake.color()
        arrivals.paint_path(dot_file, dict_values, path_id, color)
        

color_plot(f"{TEMP_PATH}/{DESIGN}.dot", dict_times, 2)
    