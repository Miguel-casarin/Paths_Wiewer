import re
from process.readSTA import Read_STA


class Info_paths:
    def __init__(self, sta_txt: str):
        # Suporta tanto texto em memória quanto caminho de arquivo
        if "\n" in sta_txt or "Startpoint:" in sta_txt:
            self.sta_content = sta_txt
        else:
            with open(sta_txt, "r") as f:
                self.sta_content = f.read()

        self.ARRIVASL_DICT = {}

    def _get_blocks(self):
        """Devolve os blocos, cada um começando em "Startpoint:"."""
        blocks = re.split(r"(?=Startpoint:)", self.sta_content)
        return [block for block in blocks if "Startpoint:" in block]

    def _entry(self, idx):
        """Garante que a chave arrival{idx} exista como dicionário."""
        return self.ARRIVASL_DICT.setdefault(f"arrival{idx}", {})

    def get_cells_paths(self):
        idx = 1
        for block in self._get_blocks():
            # Captura o padrão _NUM_ que vem sempre antes de "/" (ex: _100_/ZN, _133_/Z)
            cells = re.findall(r"_\d+_(?=/)", block)
            self._entry(idx)["cells"] = cells
            idx += 1

    def get_rises(self):
        idx = 1
        for block in self._get_blocks():
            # Captura o ^ ou v que vem antes de cada célula (ex: "^ _100_/ZN")
            rises = re.findall(r"([\^v])\s+_\d+_/", block)
            self._entry(idx)["rises"] = ["up" if r == "^" else "down" for r in rises]
            idx += 1

    def get_input(self):
        idx = 1
        for block in self._get_blocks():
            # Captura o nome da porta de entrada (ex: "N30 (in)" -> N30)
            match = re.search(r"(\S+)\s+\(in\)", block)
            self._entry(idx)["input"] = match.group(1) if match else None
            idx += 1

    def get_output(self):
        idx = 1
        for block in self._get_blocks():
            # Captura o nome da porta de saída (ex: "N431 (out)" -> N431)
            match = re.search(r"(\S+)\s+\(out\)", block)
            self._entry(idx)["output"] = match.group(1) if match else None
            idx += 1

    def get_rise_input(self):
        idx = 1
        for block in self._get_blocks():
            # Captura o ^ ou v que vem antes da porta de entrada (ex: "v N30 (in)")
            match = re.search(r"([\^v])\s+\S+\s+\(in\)", block)
            self._entry(idx)["rise_input"] = "up" if (match and match.group(1) == "^") else "down"
            idx += 1

    def get_rise_output(self):
        idx = 1
        for block in self._get_blocks():
            # Captura o ^ ou v que vem antes da porta de saída (ex: "v N431 (out)")
            match = re.search(r"([\^v])\s+\S+\s+\(out\)", block)
            self._entry(idx)["rise_output"] = "up" if (match and match.group(1) == "^") else "down"
            idx += 1

    def read_all(self):
        self.ARRIVASL_DICT = {}
        self.get_cells_paths()
        self.get_rises()
        self.get_input()
        self.get_output()
        self.get_rise_input()
        self.get_rise_output()
        return self.ARRIVASL_DICT


class Read_STA_Paths(Read_STA):
    """Herda de Read_STA sem modificar o arquivo STAout.py."""

    def get_mount_paths(self) -> dict:
        """Devolve o formato exato esperado por mountPaths.write_paths_txt."""
        steps_mount = {}
        for step, data in self.steps.items():
            steps_mount[step] = {
                "CELL": data["cell"],
                "PATHS": Info_paths(data["text"]).read_all(),
            }
        return steps_mount

    def get_formatted_paths(self) -> dict:
        """Devolve para cada step as strings montadas { 'ARRIVAL1': 'N30v -> ... -> N431v', ... }."""
        from process.mountPaths import build_arrival_line

        result = {}
        for step, data in self.steps.items():
            raw_paths = Info_paths(data["text"]).read_all()
            result[step] = {
                arrival_name.upper(): build_arrival_line(arrival)
                for arrival_name, arrival in raw_paths.items()
            }
        return result

