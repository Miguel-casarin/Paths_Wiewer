import najaeda
import re
import sys

from najaeda import netlist, naja
from collections import deque

from concurrent.futures import ThreadPoolExecutor

# retorna as features das células
class Circuit_features:
    def __init__(self, read_netlist: "Read_netlist", features_dict):
        self.read_netlist = read_netlist
        self.verilog = read_netlist.verilog
        self.library = read_netlist.library
        self.features_dict = features_dict
 
        self.top_najaeda = read_netlist.top_najaeda
        self.top = read_netlist.top
 
        self.inst_inputs = read_netlist.inst_inputs
        self.inst_outputs = read_netlist.inst_outputs
        self.inst_n_inputs = read_netlist.inst_n_inputs
        self.inst_model = read_netlist.inst_model
        self.net_drivers = read_netlist.net_drivers
        self.net_users = read_netlist.net_users
        self.pi_nets = read_netlist.pi_nets
        self.po_nets = read_netlist.po_nets

    def extract_key(self, inst_name):
        match = re.search(r'_\d+_', inst_name)
        return match.group(0) if match else None

    def compute_logic_levels(self):
        inst_inputs = self.inst_inputs
        pi_nets = self.pi_nets
        net_drivers = self.net_drivers
 
        levels = {}
        
        changed = True
 
        while changed:
            changed = False
            for inst_name, in_nets in inst_inputs.items():
                if inst_name in levels:
                    continue
 
                all_from_pi = True
                drivers_levels = []
                resolvable = True
 
                for net in in_nets:
                    if net in pi_nets:
                        continue  # entrada primária, ok
 
                    all_from_pi = False
                    drivers = net_drivers.get(net, set())
                    if not drivers:
                        resolvable = False
                        break
 
                    local_levels = []
                    for drv_name in drivers:
                        if drv_name not in levels:
                            resolvable = False
                            break
                        local_levels.append(levels[drv_name])
 
                    if not resolvable:
                        break
 
                    drivers_levels.append(max(local_levels))
 
                if not resolvable:
                    continue
 
                if all_from_pi:
                    levels[inst_name] = 1
                else:
                    levels[inst_name] = max(drivers_levels) + 1
 
                changed = True
 
        for inst_name, level in levels.items():
            key = self.extract_key(inst_name)
            if key is not None:
                self.features_dict.ad_logic_level(key, level)
 
    def comput_deep(self):
        inst_outputs = self.inst_outputs
        po_nets = self.po_nets
        net_users = self.net_users
 
        deep = {}
 
        # 1) gates diretamente ligados a uma saída primária: deep = 1
        for inst_name, out_nets in inst_outputs.items():
            if any(net in po_nets for net in out_nets):
                deep[inst_name] = 1
 
        # 2) propaga para trás: deep = 1 + max(deep dos fanouts)
        changed = True
        while changed:
            changed = False
            for inst_name, out_nets in inst_outputs.items():
                if inst_name in deep:
                    continue
 
                resolvable = True
                fanout_deeps = []
 
                for net in out_nets:
                    users = net_users.get(net, set())
                    if not users:
                        # net que não leva a lugar nenhum não contribui
                        continue
 
                    local = []
                    for u_name in users:
                        if u_name not in deep:
                            resolvable = False
                            break
                        local.append(deep[u_name])
 
                    if not resolvable:
                        break
 
                    if local:
                        fanout_deeps.append(max(local))
 
                if not resolvable or not fanout_deeps:
                    continue
 
                deep[inst_name] = max(fanout_deeps) + 1
                changed = True
 
        for inst_name, dp in deep.items():
            key = self.extract_key(inst_name)
            if key is not None:
                self.features_dict.ad_deep(key, dp)
 
    def fan_in(self):
        # para cada instância, conta quantos pinos de entrada ela possui
        for name, count in self.inst_n_inputs.items():
            key = self.extract_key(name)
            if key is not None:
                self.features_dict.ad_fanin(key, count)
 
    def fan_out(self):
        # fan-out em número de gates: quantos gates recebem essa saída
        for inst_name, out_nets in self.inst_outputs.items():
            destinations = set()
            for net in out_nets:
                for user_name in self.net_users.get(net, set()):
                    if user_name != inst_name:  # evita contar auto-loop estranho
                        destinations.add(user_name)
            
            key = self.extract_key(inst_name)
            if key is not None:
                self.features_dict.ad_fanout(key, len(destinations))

    def collect_features(self):
        self.compute_logic_levels()
        self.comput_deep()
        self.fan_in()
        self.fan_out()


# percorre o verilog com o najaeda retornando as features e cones logicos
class Read_netlist:
    def __init__(self, verilog: str, library: str):
        self.verilog = verilog
        self.library = library

        netlist.reset()
        netlist.load_liberty([self.library])
        self.top_najaeda = netlist.load_verilog([self.verilog])
    
        self.universe = naja.NLUniverse.get()
        self.top = self.universe.getTopDesign()    

        self.inst_inputs = {}
        self.inst_outputs = {}
        self.inst_n_inputs = {}
        self.inst_model = {}
        self.net_drivers = {}
        self.net_users = {}
 
        for inst in self.top.getInstances():
            name = inst.getName()
            in_nets = set()
            out_nets = set()
            n_inputs = 0
            for term in inst.getInstTerms():
                direction = term.getDirection()
                if direction == naja.SNLTerm.Direction.Input:
                    n_inputs += 1
                net = term.getNet()
                if not net:
                    continue
                if direction == naja.SNLTerm.Direction.Input:
                    in_nets.add(net)
                    self.net_users.setdefault(net, set()).add(name)
                elif direction == naja.SNLTerm.Direction.Output:
                    out_nets.add(net)
                    self.net_drivers.setdefault(net, set()).add(name)
            self.inst_inputs[name] = in_nets
            self.inst_outputs[name] = out_nets
            self.inst_n_inputs[name] = n_inputs
            self.inst_model[name] = inst.getModel().getName()
 
        self.pi_nets = set()
        self.po_nets = set()
        for term in self.top.getBitTerms():
            net = term.getNet()
            if not net:
                continue
            if term.getDirection() == naja.SNLTerm.Direction.Input:
                self.pi_nets.add(net)
            elif term.getDirection() == naja.SNLTerm.Direction.Output:
                self.po_nets.add(net)


        # conjunto de instâncias do cone de uma net de saída (só usa dicts/sets Python)
    def cone_cells(self, out_net) -> set:
        in_cone = set()
        visited = set()  # nets já expandidas
        stack = deque([out_net])
        while stack:
            net = stack.pop()

            if net in visited:
                continue
            visited.add(net)

            for drv in self.net_drivers.get(net, set()):
                in_cone.add(drv)
                for prev_net in self.inst_inputs[drv]:
                    if prev_net not in visited:
                        stack.append(prev_net)
        return in_cone

    def cones_ocurrence(self, out_pins: list, workers: int = 4) -> dict:

        # localiza as nets das saídas no thread principal (chamadas ao najaeda ficam fora das threads)
        wanted = set(out_pins)
        out_nets = {}
        for term in self.top.getBitTerms():
            net = term.getNet()
            if not net:
                continue
            if term.getName() in wanted and term.getDirection() == naja.SNLTerm.Direction.Output:
                out_nets[term.getName()] = net

        missing = wanted - out_nets.keys()
        if missing:
            raise ValueError(f"Out_PIN {sorted(missing)} not found")

        counts = {name: 0 for name in self.inst_inputs}

        # uma tarefa por saída; a contagem é feita só no thread principal (sem corrida)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for in_cone in pool.map(self.cone_cells, out_nets.values()):
                for drv in in_cone:
                    counts[drv] += 1

        return counts

    def mount_cones(self, out_pin: str, input_pin: str) -> dict:

        # contador usado para salvar os steps
        step = 1
        cone_paths = {}

        # localiza as nets da saída primária (PO) e da entrada primária (PI) pelo nome
        out_net = None
        in_net = None
        for term in self.top.getBitTerms():
            net = term.getNet()
            if not net:
                continue
            if term.getName() == out_pin and term.getDirection() == naja.SNLTerm.Direction.Output:
                out_net = net
            if term.getName() == input_pin and term.getDirection() == naja.SNLTerm.Direction.Input:
                in_net = net

        if out_net is None:
            raise ValueError(f"OUT_PIN {out_pin} NOT FOUND")
        if in_net is None:
            raise ValueError(f"INPUT PIN {input_pin} NOT FOUND")

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

            for drv in self.net_drivers.get(net, set()):
                if drv in path:
                    continue  # evita loop infinito em caso de ciclo
                for prev_net in self.inst_inputs[drv]:
                    stack.append((prev_net, path + [drv]))

        return cone_paths

    def get_features(self, features_dict) -> dict:
        circuit = Circuit_features(self, features_dict)
        circuit.collect_features()

        return circuit.features_dict
