import re
import json
import os
import sys

CELLS_LIBRARY = "./library/Nangate45_typ.lib"
OUT = "./library"

# Permite sobrescrever pelos argumentos: python makeCapacitance.py [lib] [pasta_saida]
if len(sys.argv) > 1:
    CELLS_LIBRARY = sys.argv[1]
if len(sys.argv) > 2:
    OUT = sys.argv[2]

RE_CELL = re.compile(r'^\s*cell\s*\(\s*"?([^")\s]+)"?\s*\)\s*\{')
RE_PIN = re.compile(r'^\s*pin\s*\(\s*"?([^")\s]+)"?\s*\)\s*\{')
RE_DIR = re.compile(r'^\s*direction\s*:\s*(\w+)\s*;')
RE_CAP = re.compile(r'^\s*capacitance\s*:\s*([-+0-9.eE]+)\s*;')


def parse_capacitances(path):
    """Retorna {nome_da_celula: {nome_do_pino: capacitancia}} para pinos de entrada."""
    result = {}

    cell = None          # célula atual
    cell_depth = 0       # profundidade (chaves) em que a célula foi aberta
    pin = None           # dict do pino atual
    pin_depth = 0
    depth = 0

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if cell is None:
                m = RE_CELL.match(line)
                if m:
                    cell = m.group(1)
                    cell_depth = depth
                    result[cell] = {}
                    pin = None
            else:
                m = RE_PIN.match(line)
                if m and pin is None and depth == cell_depth + 1:
                    pin = {"name": m.group(1), "direction": None, "cap": None}
                    pin_depth = depth
                elif pin is not None and depth == pin_depth + 1:
                    # só atributos diretos do pino (ignora grupos aninhados como timing)
                    m = RE_DIR.match(line)
                    if m:
                        pin["direction"] = m.group(1)
                    m = RE_CAP.match(line)
                    if m:
                        pin["cap"] = float(m.group(1))

            depth += line.count("{") - line.count("}")

            # fechou o pino
            if pin is not None and depth <= pin_depth:
                if pin["direction"] == "input" and pin["cap"] is not None:
                    result[cell][pin["name"]] = pin["cap"]
                pin = None

            # fechou a célula
            if cell is not None and depth <= cell_depth:
                cell = None

    return result


def main():
    caps = parse_capacitances(CELLS_LIBRARY)

    os.makedirs(OUT, exist_ok=True)
    out_file = os.path.join(OUT, "capacitance.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(caps, f, indent=4)

    sem_entrada = [c for c, v in caps.items() if not v]
    print(f"{len(caps)} células -> {out_file}")
    if sem_entrada:
        print(f"{len(sem_entrada)} sem pino de entrada: {', '.join(sem_entrada)}")


if __name__ == "__main__":
    main()
