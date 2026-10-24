import re


class Search_steps:

    def __init__(self, dot_file: str, steps_file: str):

        self.dot_file = dot_file
        self.steps_file = steps_file
    
    def count_steps(self) -> list:
        steps = []
        with open(self.steps_file, "r", encoding="utf-8") as f:
            for line in f:
                m = re.match(r"^STEP\s+(\d+)\s*$", line)
                if m:
                    steps.append(int(m.group(1)))

        return steps

    def arrivals_by_step(self, step: int) -> dict:
        arrivals = {}
        in_step = False
        arrival = None
 
        with open(self.steps_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
 
                m = re.match(r"^STEP\s+(\d+)$", line)
                if m:
                    if in_step:      # começou o próximo step: já terminou
                        break
                    in_step = int(m.group(1)) == step
                    continue
 
                if not in_step:
                    continue
 
                m = re.match(r"^(ARRIVAL\d+):$", line)
                if m:
                    arrival = m.group(1)
                elif arrival and "->" in line:
                    arrivals[arrival] = line
                    arrival = None
 
        return arrivals

    def previos_arrivals(self, step: int) -> dict:
        if step != 0:
            arrivals = self.arrivals_by_step(step - 1)
        else:
            print("step igual a zero")
            arrivals = {}

        return arrivals

    def return_step(self, step: int) -> str:
        with open(self.steps_file, "r", encoding="utf-8") as f:
            text = f.read()

        pattern = rf"^STEP {step}\n.*?(?=^STEP \d+\n|\Z)"
        match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
        if match is None:
            raise ValueError(f"STEP {step} não encontrado em {self.steps_file}")

        return match.group(0).rstrip("\n")
        