import os 
import json
import sys
import pprint

from gui import app
from gui.shell import log_shell
from process import readVerilog, ReadNetlist, editTCL, readSTA
from run import runSTA
from utils import files, SaveFeatures

NUMBER_THREADS = os.cpu_count() - 1

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

try:
    design_info = readVerilog.Gates_info(f"{VERILOGS}/{DESIGN}.v")
    cells_ids = design_info.get_cells_ids()
    cells_types = design_info.logic_cells_type()
except Exception as error:
    print(f"[ERROR] TO GET NETLIST CELLS INFO :\n{error}")
    sys.exit(1)

# coletando as features
features_dict = SaveFeatures.Save_features()

try:
    features_dict.fild_dictionary(cells_ids, cells_types)
except Exception as error:
    print(f"[ERROR] TO FILD DICT:\n {error}")
    sys.exit(1)

try: 
    netlist = ReadNetlist.Read_netlist(f"{VERILOGS}/{DESIGN}.v", f"{LIBRARY_PATH}/{LIBRARY}")
    netlist.get_features(features_dict)

    cones_count = netlist.cones_ocurrence(design_outputs, NUMBER_THREADS)
    for cell_id in cells_ids:
        features_dict.ad_cone(cell_id, cones_count.get(cell_id, 0))

except Exception as error:
    print(f"[ERROR] TO GET FEATURES:\n {error}")
    sys.exit(1)

# gtk 0
files.copy_rename(f"{TCL_PATH}/timing.tcl", f"gtk0_{DESIGN}.tcl", TEMP_PATH)
base_step_tcl = f"{TEMP_PATH}/gtk0_{DESIGN}.tcl"

try:
    editTCL.edit_liberty(base_step_tcl, f"{LIBRARY_PATH}/{LIBRARY}")
    editTCL.edit_verilog(base_step_tcl, f"{VERILOGS}/{DESIGN}.v")
    editTCL.edit_link_design(base_step_tcl, design_module)
    editTCL.parse_inputs(base_step_tcl, design_inputs)
    editTCL.parse_outputs(base_step_tcl, design_outputs)
    editTCL.paths_total(base_step_tcl, len(design_outputs))
except Exception as error:
    print(f"[ERROR] TO EDIT BASE TCL :\n{error}")
    sys.exit(1)

gtk0_output = runSTA.run_sta(base_step_tcl)

try:
    base = readSTA.Read_sta(gtk0_output)
    base_power = base.get_power()
    base_arrivals = base.get_arrival_times()
    base_paths = base.ocurence_by_paths()
except Exception as error:
    print(f"[ERROR] TO READ GTK 0 :\n{error}")
    sys.exit(1)

print(base_power)
print(base_arrivals)
print(base_paths)

