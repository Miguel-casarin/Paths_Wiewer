import re

class Read_sta:
    def __init__(self, sta_output: str):
        self.sta_output = sta_output

    def get_arrival_times(self) -> dict:
        arrivals = {}
        path_id = 0
        current_arrival = None
        inside_path = False

        for line in self.sta_output.splitlines():
            line = line.strip()

            if line.startswith("Startpoint:"):
                # salva o caminho anterior
                if current_arrival is not None:
                    arrivals[path_id] = current_arrival

                path_id += 1
                current_arrival = None
                inside_path = True

            elif "data arrival time" in line and inside_path:
                if current_arrival is None:  # pega só o primeiro
                    value = float(line.split()[0])
                    if value > 0:
                        current_arrival = value

        # salva o último caminho
        if current_arrival is not None:
            arrivals[path_id] = current_arrival

        return arrivals

    def get_cells(self) -> dict:
        pcritic_id = 0
        result = {}

        pattern_cells = re.compile(r"(_\d+_)/")

        for line in self.sta_output.splitlines():
            line = line.strip()

            if line.startswith("Startpoint"):
                pcritic_id += 1
                result[pcritic_id] = []
                continue

            match = pattern_cells.search(line)
            if match and pcritic_id > 0:
                result[pcritic_id].append(match.group(1))

        return result


    # retorna a ocorrência de um dado gate em todos os caminhos críticos do sta
    def ocurence_by_paths(self) -> dict:
        result = {}
        pattern_cells = re.compile(r"(_\d+_)/")

        for line in self.sta_output.splitlines():
            line = line.strip()

            match = pattern_cells.search(line)
            if match:
                cell_id = match.group(1)

                if cell_id not in result:
                    result[cell_id] = 0

                result[cell_id] += 1

        return result

    def get_power(self) -> float | None:
        pattern = re.compile(r"^Total\s+(?:\S+\s+){3}(\S+)", re.MULTILINE)

        match = pattern.search(self.sta_output)

        if match:
            return float(match.group(1))
        return None

    
class Read_steps:
    def __init__(self, sta_out):
        self.sta_out = sta_out

        # divide a saída por step: {step: {"cell": célula dimensionada, "text": texto do step}}
        self.steps = {}
        blocks = re.split(r"^STEP:\s*(\d+)\s*$", sta_out, flags=re.MULTILINE)
        # blocks = [cabeçalho, '1', texto1, '2', texto2, ...]

        for step, text in zip(blocks[1::2], blocks[2::2]):
            cell = re.search(r"^sized cell:\s*(\S+)", text, flags=re.MULTILINE)
            self.steps[int(step)] = {
                "cell": cell.group(1) if cell else None,
                "text": text,
            }

    def get_steps(self):
        return list(self.steps)

    def get_sized_cells(self):
        return {step: data["cell"] for step, data in self.steps.items()}

    def get_arrival_times(self):
        by_step = {}

        for step, data in self.steps.items():
            arrivals = {}
            path_id = 0
            current_arrival = None
            inside_path = False

            for line in data["text"].splitlines():
                line = line.strip()

                if line.startswith("Startpoint:"):
                    # salva o caminho anterior
                    if current_arrival is not None:
                        arrivals[path_id] = current_arrival

                    path_id += 1
                    current_arrival = None
                    inside_path = True

                elif "data arrival time" in line and inside_path:
                    if current_arrival is None:  # pega só o primeiro
                        value = float(line.split()[0])
                        if value > 0:
                            current_arrival = value

            # salva o último caminho
            if current_arrival is not None:
                arrivals[path_id] = current_arrival

            by_step[step] = arrivals

        return by_step

    def get_cells(self):
        by_step = {}
        pattern_cells = re.compile(r"(_\d+_)/")

        for step, data in self.steps.items():
            pcritic_id = 0
            result = {}

            for line in data["text"].splitlines():
                line = line.strip()

                if line.startswith("Startpoint"):
                    pcritic_id += 1
                    result[pcritic_id] = []
                    continue

                match = pattern_cells.search(line)
                if match and pcritic_id > 0:
                    result[pcritic_id].append(match.group(1))

            by_step[step] = result

        return by_step

    def paths(self):
        # para cada caminho (1, 2, 3 ...) lista, em ordem, os ids das células
        by_step = {}
        pattern_cells = re.compile(r"(_\d+_)/")

        for step, data in self.steps.items():
            path_id = 0
            result = {}

            for line in data["text"].splitlines():
                line = line.strip()

                if line.startswith("Startpoint:"):
                    path_id += 1
                    result[path_id] = []
                    continue

                match = pattern_cells.search(line)
                if match and path_id > 0:
                    result[path_id].append(match.group(1))

            by_step[step] = result

        return by_step

    def get_input(self):
        # para cada caminho (1, 2, 3 ...) pega a porta de entrada, ex.: "0.00085  0.00085 v N6 (in)" -> N6
        by_step = {}
        pattern_input = re.compile(r"-?\d+\.\d+\s+-?\d+\.\d+\s+[v^]\s+(\S+)\s+\(in\)")

        for step, data in self.steps.items():
            path_id = 0
            result = {}

            for line in data["text"].splitlines():
                line = line.strip()

                if line.startswith("Startpoint:"):
                    path_id += 1
                    result[path_id] = None
                    continue

                match = pattern_input.match(line)
                if match and path_id > 0:
                    result[path_id] = match.group(1)

            by_step[step] = result

        return by_step

    def get_output(self):
        # para cada caminho (1, 2, 3 ...) pega a porta de saída, ex.: "0.00000  0.06235 ^ N23 (out)" -> N23
        by_step = {}
        pattern_output = re.compile(r"-?\d+\.\d+\s+-?\d+\.\d+\s+[v^]\s+(\S+)\s+\(out\)")

        for step, data in self.steps.items():
            path_id = 0
            result = {}

            for line in data["text"].splitlines():
                line = line.strip()

                if line.startswith("Startpoint:"):
                    path_id += 1
                    result[path_id] = None
                    continue

                match = pattern_output.match(line)
                if match and path_id > 0:
                    result[path_id] = match.group(1)

            by_step[step] = result

        return by_step


    def get_power(self):
        by_step = {}
        pattern = re.compile(r'^Total\s+(?:\S+\s+){3}(\S+)', re.MULTILINE)

        for step, data in self.steps.items():
            match = pattern.search(data["text"])

            if match:
                by_step[step] = float(match.group(1))
            else:
                by_step[step] = None

        return by_step

    def get_all(self):
        # tudo num único dicionário, com o step como chave (uma passada por step)
        by_step = {}
        pattern_cells = re.compile(r"(_\d+_)/")
        pattern_power = re.compile(r'^Total\s+(?:\S+\s+){3}(\S+)', re.MULTILINE)
        pattern_input = re.compile(r"-?\d+\.\d+\s+-?\d+\.\d+\s+[v^]\s+(\S+)\s+\(in\)")
        pattern_output = re.compile(r"-?\d+\.\d+\s+-?\d+\.\d+\s+[v^]\s+(\S+)\s+\(out\)")

        for step, data in self.steps.items():
            arrivals = {}
            cells = {}
            count = {}
            ocurence = {}
            inputs = {}
            outputs = {}
            path_id = 0
            current_arrival = None
            inside_path = False
            counting = True  # count_ocurence_path só vale para o primeiro caminho

            for line in data["text"].splitlines():
                line = line.strip()

                if line.startswith("Startpoint:"):
                    # salva o caminho anterior
                    if current_arrival is not None:
                        arrivals[path_id] = current_arrival

                    path_id += 1
                    current_arrival = None
                    inside_path = True
                    cells[path_id] = []
                    inputs[path_id] = None
                    outputs[path_id] = None
                    continue

                match = pattern_input.match(line)
                if match and path_id > 0:
                    inputs[path_id] = match.group(1)

                match = pattern_output.match(line)
                if match and path_id > 0:
                    outputs[path_id] = match.group(1)

                match = pattern_cells.search(line)
                if match and path_id > 0:
                    cell_id = match.group(1)
                    cells[path_id].append(cell_id)
                    ocurence[cell_id] = ocurence.get(cell_id, 0) + 1
                    if counting:
                        count[cell_id] = count.get(cell_id, 0) + 1

                if "data arrival time" in line:
                    counting = False  # fim da listagem do primeiro caminho
                    if inside_path and current_arrival is None:  # pega só o primeiro
                        value = float(line.split()[0])
                        if value > 0:
                            current_arrival = value

            # salva o último caminho
            if current_arrival is not None:
                arrivals[path_id] = current_arrival

            power = pattern_power.search(data["text"])

            by_step[step] = {
                "cell": data["cell"],
                "power": float(power.group(1)) if power else None,
                "arrival_times": arrivals,
                "arrivals": cells,
                "input": inputs,
                "output": outputs,
                "previos": 0,
                "curente": 0
            }

        return by_step