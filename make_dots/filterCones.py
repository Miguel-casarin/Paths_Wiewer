import json
import re
import shutil
from pathlib import Path


class Mount_cones:
    def __init__(self, inputs_list: list, dot_file: str, json_cones: str):
        self.inputs_list = inputs_list 
        self.dot_file = dot_file
        self.json_cones = json_cones
        self.temp_dir = "./temp"

    def take_name(self) -> str:
        return Path(self.dot_file).stem
    
    def compy_dot(self, output: str) -> str:
        name = self.take_name()
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)
        dest_file = f"{self.temp_dir}/{name}_{output}.dot"
        shutil.copyfile(self.dot_file, dest_file)
        return dest_file

    def make_dot(self, output: str) -> str:
        new_dot = self.compy_dot(output)

        if isinstance(self.json_cones, (str, Path)):
            with open(self.json_cones, "r") as f:
                json_data = json.load(f)
        else:
            json_data = self.json_cones

        output_data = json_data.get(output, {})

        # Identifica todas as entradas que possuem caminhos para este output (campos não vazios)
        valid_inputs = {inp for inp, paths in output_data.items() if paths}

        # Coleta todas as células pertencentes aos caminhos até o output
        valid_cells = set()
        for inp in valid_inputs:
            paths = output_data[inp]
            for step_key, cells in paths.items():
                valid_cells.update(cells)

        with open(new_dot, "r") as f:
            lines = f.readlines()

        header_lines = []
        port_lines = []
        cell_lines = []
        edge_lines = []

        kept_ports = {}
        kept_cells = {}

        port_pattern = re.compile(r'^\s*([a-zA-Z0-9_]+)\s*\[\s*shape=octagon,\s*label="([^"]+)"')
        cell_pattern = re.compile(r'^\s*([a-zA-Z0-9_]+)\s*\[\s*shape=record,\s*label="([^"]+)"')
        edge_pattern = re.compile(r'^\s*([a-zA-Z0-9_]+)(?::[a-zA-Z0-9_]+)*\s*->\s*([a-zA-Z0-9_]+)(?::[a-zA-Z0-9_]+)*')

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.startswith("digraph") or stripped.startswith("label=") or stripped.startswith("rankdir=") or stripped.startswith("remincross="):
                header_lines.append(line)
                continue

            if stripped == "}":
                continue

            port_match = port_pattern.match(line)
            if port_match:
                node_id = port_match.group(1)
                port_label = port_match.group(2)
                if port_label in valid_inputs or port_label == output:
                    kept_ports[node_id] = port_label
                    port_lines.append(line)
                continue

            cell_match = cell_pattern.match(line)
            if cell_match:
                node_id = cell_match.group(1)
                cell_id_match = re.search(r'\|\s*(_\w+_)\s*(?:\\n|\n|[|])', line)
                cell_id = cell_id_match.group(1) if cell_id_match else None
                if cell_id and cell_id in valid_cells:
                    kept_cells[node_id] = cell_id
                    cell_lines.append(line)
                continue

            edge_match = edge_pattern.match(line)
            if edge_match:
                src_id = edge_match.group(1)
                dst_id = edge_match.group(2)
                edge_lines.append((src_id, dst_id, line))
                continue

        kept_nodes = set(kept_ports.keys()).union(set(kept_cells.keys()))

        filtered_edge_lines = [
            line for src_id, dst_id, line in edge_lines
            if src_id in kept_nodes and dst_id in kept_nodes
        ]

        # Mantém o padrão com inputs na esquerda (rank=source) e outputs na direita (rank=sink)
        source_nodes = [node_id for node_id, label in kept_ports.items() if label in valid_inputs]
        sink_nodes = [node_id for node_id, label in kept_ports.items() if label == output]

        rank_lines = []
        if source_nodes:
            rank_lines.append(f'{{ rank=source; {" ".join(source_nodes)}; }}\n')
        if sink_nodes:
            rank_lines.append(f'{{ rank=sink; {" ".join(sink_nodes)}; }}\n')

        with open(new_dot, "w") as f:
            for h in header_lines:
                f.write(h)
            f.write("\n")

            for r in rank_lines:
                f.write(r)
            if rank_lines:
                f.write("\n")

            for p in port_lines:
                f.write(p)
            if port_lines:
                f.write("\n")

            for c in cell_lines:
                f.write(c)
            if cell_lines:
                f.write("\n")

            for e in filtered_edge_lines:
                f.write(e)

            f.write("}\n")

        return new_dot