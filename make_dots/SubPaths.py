import re


class DotSubgraph:
    """
    Reads a Graphviz .dot netlist and writes a new .dot that contains only:
      - the selected gates (e.g. the keys returned by show_dif);
      - the nodes that drive them (their input gates and input ports).

    Wires between two selected gates are drawn in red; wires coming from the
    input nodes keep their original color.
    """

    EDGE_RE = re.compile(r"^\s*(\S+)\s*->\s*(\S+)\s*\[(.*)\]\s*;\s*$")
    NODE_RE = re.compile(r"^\s*(\w+)\s*\[(.*)\]\s*;\s*$")
    # cell label: {{<A1> in1|<A2> in2}|_140_\nNAND2_X1|{<ZN> ZN}}  -> "_140_"
    GATE_NAME_RE = re.compile(r"\}\|([^|]*?)\\n")
    LABEL_RE = re.compile(r'label="([^"]+)"')

    def __init__(self, dot_file: str):
        self.dot_file = dot_file
        self.header = []        # lines before the first node (digraph, rankdir, ...)
        self.nodes = {}         # node id ("c1") -> original line
        self.gate_to_node = {}  # gate name ("_140_") -> node id ("c1")
        self.edges = []         # (source node id, target node id, original line)
        self._parse()

    def _parse(self):
        with open(self.dot_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")

                edge = self.EDGE_RE.match(line)
                if edge:
                    # "c9:ZN:e" -> "c9" ; "p0:e" -> "p0"
                    source = edge.group(1).split(":")[0]
                    target = edge.group(2).split(":")[0]
                    self.edges.append((source, target, line))
                    continue

                node = self.NODE_RE.match(line)
                if node:
                    node_id = node.group(1)
                    self.nodes[node_id] = line
                    gate = self.GATE_NAME_RE.search(node.group(2))
                    if gate:
                        self.gate_to_node[gate.group(1).strip()] = node_id
                    else:
                        lbl = self.LABEL_RE.search(node.group(2))
                        if lbl:
                            self.gate_to_node[lbl.group(1).strip()] = node_id
                    continue

                stripped = line.strip()
                if stripped and stripped != "}" and not self.nodes and not self.edges:
                    self.header.append(line)

    def generate(self, gates, output_file: str) -> str:
        """
        gates: dict (keys are the gate names, e.g. the show_dif result) or any
               iterable of gate names such as "_146_".
        Writes the new .dot to output_file and returns its path.
        """
        gates = set(gates)
        unknown = gates - self.gate_to_node.keys()
        if unknown:
            raise ValueError(f"Gates not found in {self.dot_file}: {sorted(unknown)}")

        selected = {self.gate_to_node[gate] for gate in gates}
        input_nodes = set()
        kept_edges = []

        for source, target, line in self.edges:
            if target not in selected:
                continue
            if source in selected:
                # wire between two selected gates -> red
                line, count = re.subn(r'(?<!font)color="[^"]*"', 'color="red"', line)
                if count == 0:
                    line = line.replace("[", '[color="red", ', 1)
            else:
                input_nodes.add(source)
            kept_edges.append(line)

        keep = selected | input_nodes
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(self.header) + "\n\n")
            for node_id, line in self.nodes.items():
                if node_id in keep:
                    f.write(line + "\n")
            f.write("\n")
            for line in kept_edges:
                f.write(line + "\n")
            f.write("}\n")

        return output_file