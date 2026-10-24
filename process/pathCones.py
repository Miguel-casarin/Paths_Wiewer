import najaeda
from collections import deque
from najaeda import netlist, naja


def get_cones(output: str, input: str, verilog: str, libraey: str) -> dict:

    # carregando o najaeda 
    netlist.reset()
    netlist.load_liberty([libraey])
    top_najaeda = netlist.load_verilog([verilog])

    universe = naja.NLUniverse.get()
    top = universe.getTopDesign()

    # contador usado para salvar os steps
    step = 1
    cone_paths = {}

    # localiza as nets da saída primária (PO) e da entrada primária (PI) pelo nome
    out_net = None
    in_net = None
    for term in top.getBitTerms():
        net = term.getNet()
        if not net:
            continue
        if term.getName() == output and term.getDirection() == naja.SNLTerm.Direction.Output:
            out_net = net
        if term.getName() == input and term.getDirection() == naja.SNLTerm.Direction.Input:
            in_net = net

    if out_net is None:
        raise ValueError(f"Saída '{output}' não encontrada")
    if in_net is None:
        raise ValueError(f"Entrada '{input}' não encontrada")

    # mapeia:
    #  - inst_name -> conjunto de nets de entrada
    #  - net -> instâncias que a dirigem (fanin)
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