import os 
import json
import sys
import pprint

from gui import app
from gui.shell import log_shell
from process import readVerilog, ReadNetlist
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

netlist = ReadNetlist.Read_netlist(f"{VERILOGS}/{DESIGN}.v", f"{LIBRARY_PATH}/{LIBRARY}")
netlist.get_features(features_dict)


cones_count = netlist.cones_ocurrence(design_outputs, NUMBER_THREADS)
for cell_id in cells_ids:
    features_dict.ad_cone(cell_id, cones_count.get(cell_id, 0))


pprint.pprint(features_dict.nets_and_topology)