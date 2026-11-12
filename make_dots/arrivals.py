import re


def paint_path(dot_file, paths, key, rgb):
    """Edita o .dot existente (no proprio arquivo): pinta os gates de um caminho
    do STA e escreve o Time dentro deles.

    dot_file : caminho do .dot gerado pelo verilog_to_dot
    paths    : dicionario do Read_paths.get_paths() -> {1: {"_100_": 0.01728, ...}, ...}
    key      : chave do caminho (arrival) a pintar, ex.: 1
    rgb      : cor como lista [R, G, B] (0-255), ex.: [255, 165, 0] = laranja
    """
    if key not in paths:
        raise KeyError(f"Caminho {key} nao existe. Chaves disponiveis: {list(paths)}")
    if len(rgb) != 3 or not all(0 <= int(c) <= 255 for c in rgb):
        raise ValueError("rgb deve ser uma lista [R, G, B] com valores de 0 a 255")

    times = paths[key]  # {"_100_": time, ...}
    color = "#{:02x}{:02x}{:02x}".format(*(int(c) for c in rgb))

    # aceita no ja pintado antes (style/fillcolor e Time ja escritos) para poder repintar
    pat_node = re.compile(r'^(c\d+) \[ shape=record,(?: style=filled, fillcolor="[^"]*",)? label="(.*)" \];$')
    pat_name = re.compile(r"\|(_\d+_)\\n(\w+)(?:\\n[\d.]+)?\|")  # |_100_\nINV_X1| ou |_100_\nINV_X1\n0.01728|
    found = set()
    new_lines = []

    with open(dot_file, encoding="utf-8") as f:
        lines = f.read().splitlines()

    for line in lines:
        m = pat_node.match(line)
        if m:
            node, label = m.groups()
            nm = pat_name.search(label)
            if nm and nm.group(1) in times:
                cell, ctype = nm.groups()
                found.add(cell)
                label = pat_name.sub(
                    lambda _: f"|{cell}\\n{ctype}\\n{times[cell]:.5f}|", label, count=1)
                line = (f'{node} [ shape=record, style=filled, fillcolor="{color}", '
                        f'label="{label}" ];')
        new_lines.append(line)

    missing = set(times) - found
    if missing:
        print(f"Aviso: celulas do caminho {key} nao encontradas no dot: {sorted(missing)}")

    with open(dot_file, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")