import os 
import json
import sys
import pprint

from gui import app
from gui.shell import log_shell
from process import readVerilog, ReadNetlist, editTCL, readSTA, getCones
from run import runSTA, runSteps
from utils import files, SaveFeatures, divide
from make_dots import circuitDot

NUMBER_THREADS = os.cpu_count() - 1

while True:
    circuit = input("DESIGN TO RUN : ").strip()
    if not circuit.endswith(".v"):
        circuit += ".v"          # aceita "c17" ou "c17.v"
    if files.file_exists("verilogs", circuit):
        break
    print(f"File '{circuit}' not found in verilogs/. Try again.")

DESIGN = circuit[:-2]
PRIORITY_FILE = f"{DESIGN}_priority.txt"
VERILOGS = "./verilogs"
LIBRARY = "Nangate45_typ.lib"
LIBRARY_PATH = "./library"
TCL_PATH = "./tcl"
TEMP_PATH = "./temp"

SIZE_PROCESS = {}

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

#######################
# Executando os steps #

# Lista de prioridades
CELLS_TO_UPSIZE = files.returns_cells_steps(f"./input/{PRIORITY_FILE}")
works_number = divide.define_threads(NUMBER_THREADS, CELLS_TO_UPSIZE)

works_indexs = divide.particion_list(CELLS_TO_UPSIZE, works_number)
steps_starter = divide.starter_steps(works_number, CELLS_TO_UPSIZE)

# cria os tcls
maker = runSteps.Make_TCL_Steps(
    tcl_template=f"{TCL_PATH}/sizeParallel.tcl",
    verilog_path=f"{VERILOGS}/{DESIGN}.v",
    lib_path=f"{LIBRARY_PATH}/{LIBRARY}",
    module=design_module,
    inputs_list=design_inputs,
    outputs_list=design_outputs,
    cells_to_upsize=CELLS_TO_UPSIZE,
    design=DESIGN,
    temp_path=TEMP_PATH,
)

step_tcls = []
for step, (start, end) in zip(steps_starter, works_indexs):
    step_tcls.append(maker.build(step, start, end))

# roda o OpenSTA em paralelo
runner = runSteps.Run_Steps(
    base_power=base_power,
    base_arrivals=base_arrivals,
    results=SIZE_PROCESS,
    max_workers=NUMBER_THREADS,
)
runner.run(step_tcls)


# verifica se o .dot existe caso ele não exista um e criado em ./input
dot_exists = files.file_exists("./input", f"{DESIGN}.dot")
cone_exists = files.file_exists("./input", f"cones_{DESIGN}.json")

if dot_exists:
    pass
else:
    circuitDot.verilog_to_dot(f"{VERILOGS}/{DESIGN}.v", "./input")

if cone_exists:
    pass
else:
    getCones.mout_cones(LIBRARY, DESIGN, "./input")


app.App(features_dict=features_dict, size_process=SIZE_PROCESS).mainloop()