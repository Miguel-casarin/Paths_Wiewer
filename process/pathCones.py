import najaeda
import threading
from collections import deque
from najaeda import netlist, naja

_cache = {}
_lock = threading.Lock()


def _get_design_data(verilog: str, library: str):
    key = (verilog, library)
    with _lock:
        if key in _cache:
            return _cache[key]

        netlist.reset()
        netlist.load_liberty([library])
        top_najaeda = netlist.load_verilog([verilog])

        universe = naja.NLUniverse.get()
        top = universe.getTopDesign()

        terms = {}
        for term in top.getBitTerms():
            net = term.getNet()
            if net:
                terms[(term.getName(), term.getDirection())] = net

        inst_inputs = {}
        net_drivers = {}
        for inst in top.getInstances():
            name = inst.getName()
            in_nets = set()
            for term in inst.getInstTerms():
                net = term.getNet()
                if not net:
                    continue
                if term.getDirection() == naja.SNLTerm.Direction.Input:
                    in_nets.add(net)
                elif term.getDirection() == naja.SNLTerm.Direction.Output:
                    net_drivers.setdefault(net, set()).add(name)
            inst_inputs[name] = in_nets

        _cache[key] = (terms, inst_inputs, net_drivers)
        return _cache[key]


def get_cones(output: str, input: str, verilog: str, libraey: str) -> dict:
    terms, inst_inputs, net_drivers = _get_design_data(verilog, libraey)

    out_net = terms.get((output, naja.SNLTerm.Direction.Output))
    in_net = terms.get((input, naja.SNLTerm.Direction.Input))

    if out_net is None:
        raise ValueError(f"Saída '{output}' não encontrada")
    if in_net is None:
        raise ValueError(f"Entrada '{input}' não encontrada")

    # contador usado para salvar os steps
    step = 1
    cone_paths = {}

    # percorre do PO para trás até o PI (DFS iterativo)
    # cada item da pilha: (net atual, células já percorridas, da saída para a entrada)
    stack = deque([(out_net, [])])
    while stack:
        net, path = stack.pop()

        # chegou no PI: salva as células do caminho e incrementa o step
        if net == in_net:
            cone_paths[step] = path
            step += 1
            continue

        for drv in net_drivers.get(net, set()):
            if drv in path:
                continue  # evita loop infinito em caso de ciclo
            for prev_net in inst_inputs[drv]:
                stack.append((prev_net, path + [drv]))

    return cone_paths