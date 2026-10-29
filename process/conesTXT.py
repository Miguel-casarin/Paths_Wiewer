import os


def save_cones_txt(geral: dict, out_path: str) -> None:
    """
    Recebe o dicionário 'geral' contendo os cones mapeados por saída e entrada:
        geral[out][inp] = {step: [células do caminho da saída para a entrada]}
    
    Salva em arquivo texto no formato:
        <entrada> -> <célula 1> -> <célula 2> -> ... -> <saída>
    """
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        for out, inputs in geral.items():
            for inp, paths in inputs.items():
                if isinstance(paths, dict):
                    path_list = paths.values()
                elif isinstance(paths, list):
                    path_list = paths
                else:
                    continue

                for path in path_list:
                    # As células em 'path' foram coletadas da saída para a entrada (PO -> PI).
                    # Invertemos para manter a ordem da entrada para a saída (PI -> PO).
                    cells = path[::-1]
                    line_nodes = [str(inp)] + [str(c) for c in cells] + [str(out)]
                    f.write(" -> ".join(line_nodes) + "\n")
