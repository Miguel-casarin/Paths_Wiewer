from . import readVerilog, pathCones


import json


def mout_cones(lib, design, save_dir):

    circuit_io = readVerilog.Get_IO(f"./verilogs/{design}.v")
    design_inputs = circuit_io.get_inputs()
    design_outputs = circuit_io.get_outputs()

    geral = {}

    for out in design_outputs:
        paths = {}
        for inp in design_inputs:
            t = pathCones.get_cones(out, inp, f"./verilogs/{design}.v", f"./library/{lib}")
            paths[inp] = t

        geral[out] = paths

    #pprint.pprint(geral)

    with open(f"{save_dir}/cones_{design}.json", "w") as f:
        json.dump(geral, f, indent=4)