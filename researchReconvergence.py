from concurrent.futures import ThreadPoolExecutor
from process import readVerilog, pathCones

import sys
import os
import pprint
import time

NUMBER_THREADS = os.cpu_count() - 1
VERILOGS = "./verilogs"
LIBRARY = "Nangate45_typ.lib"
LIBRARY_PATH = "./library"
DESIGN = "c7552" 

s = time.perf_counter()

# inputs, outputs, cells, logic types
try:
    design_io = readVerilog.Get_IO(f"{VERILOGS}/{DESIGN}.v")
    design_module = design_io.verilog_module()
    design_inputs = design_io.get_inputs()
    design_outputs = design_io.get_outputs()
except Exception as error:
    print(f"[ERROR] TO GET IO :\n{error}")
    sys.exit(1)

geral = {out: {} for out in design_outputs}
verilog_file = f"{VERILOGS}/{DESIGN}.v"
library_file = f"{LIBRARY_PATH}/{LIBRARY}"

def fetch_cone(out, inp):
    return out, inp, pathCones.get_cones(out, inp, verilog_file, library_file)

with ThreadPoolExecutor(max_workers=NUMBER_THREADS) as executor:
    futures = [
        executor.submit(fetch_cone, out, inp)
        for out in design_outputs
        for inp in design_inputs
    ]
    for future in futures:
        out, inp, t = future.result()
        geral[out][inp] = t



def previos_gates(gates_list: list, gate: str, pin_input: str) -> list:
    pos = gates_list.index(gate)
    return [pin_input] + gates_list[:pos]


def research_reconvergence(paths_dict: dict, gate: str) -> list:
    paths = []

    for out_pin, in_pins in paths_dict.items():
        for in_pin, path in in_pins.items():
            for num_path, gates_list in path.items():
                if gate in gates_list:
                    paths.append(previos_gates(gates_list, gate, in_pin))

    return paths


def remove_duplicates(paths: list) -> list:
    unique = []

    for path in paths:
        if path not in unique:
            unique.append(path)

    return unique

paths = research_reconvergence(geral, '_1301_')
unique_paths = remove_duplicates(paths)

for path in unique_paths:
    print(f"\n{path}")

f = time.perf_counter()
print(f"\nRuning Time: {f - s:.2f} s")