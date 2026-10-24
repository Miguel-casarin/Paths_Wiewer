ARROW = {"up": "^", "down": "v"}


def _arrow(rise):
    # None (nao encontrado no STA) vira "?" em vez de quebrar com KeyError
    return ARROW.get(rise, "?")


def _build_arrival_line(arrival):
    nodes = []

    nodes.append(f"{arrival['input']}{_arrow(arrival['rise_input'])}")

    for cell, rise in zip(arrival["cells"], arrival["rises"]):
        nodes.append(f"{cell}{_arrow(rise)}")

    nodes.append(f"{arrival['output']}{_arrow(arrival['rise_output'])}")

    return " -> ".join(nodes)


def _paths_from_all(data: dict) -> dict:
    """
    Converte um item do get_all() (Read_steps[step] ou Read_sta) em
    {"arrival1": {cells, rises, input, output, rise_input, rise_output}, ...}
    """
    paths = {}

    for path_id, cells in data["arrivals"].items():
        paths[f"arrival{path_id}"] = {
            "cells": cells,
            "rises": data["rises"].get(path_id, []),
            "input": data["input"].get(path_id),
            "output": data["output"].get(path_id),
            "rise_input": data["rise_input"].get(path_id),
            "rise_output": data["rise_output"].get(path_id),
        }

    return paths


def build_steps(all_steps: dict, base_all: dict | None = None) -> dict:
    """
    Recebe o retorno de Read_steps(...).get_all() e, opcionalmente, o de
    Read_sta(...).get_all() (baseline). Devolve
    {step: {"CELL": celula dimensionada, "PATHS": {arrivalN: {...}}}}
    com o baseline como step 0 (CELL = 0) antes dos demais.
    """
    steps = {}

    if base_all is not None:
        steps[0] = {"CELL": 0, "PATHS": _paths_from_all(base_all)}

    for step, data in all_steps.items():
        steps[step] = {"CELL": data["cell"], "PATHS": _paths_from_all(data)}

    return steps


def write_paths_txt(steps: dict, out_path: str):
    """
    Recebe o dicionario STEPS (formato {step: {CELL, PATHS: {arrivalN: {...}}}},
    ja com o step 0 se vier de build_steps(..., base_all)) e escreve o caminho
    de cada arrival em out_path, com ^ para "up" e v para "down".
    """
    with open(out_path, "w") as f:
        for step, step_data in steps.items():
            f.write(f"STEP {step}\n")
            f.write(f"CELL: {step_data['CELL']}\n")

            for arrival_name, arrival in step_data["PATHS"].items():
                f.write(f"{arrival_name.upper()}:\n")
                f.write(f"{_build_arrival_line(arrival)}\n\n")

            f.write("\n")