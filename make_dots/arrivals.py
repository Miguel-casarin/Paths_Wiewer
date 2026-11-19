import re


def paint_path(dot_file, paths, key, rgb):
    """Edita o .dot existente (no proprio arquivo): pinta os gates de um caminho
    do STA e escreve o Delay e o Time dentro deles.

    dot_file : caminho do .dot gerado pelo verilog_to_dot
    paths    : dicionario do Read_paths.get_paths() -> {1: {"_100_": {"delay": 0.01645, "time": 0.01728}, ...}, ...}
    key      : chave do caminho (arrival) a pintar, ex.: 1
    rgb      : cor como lista [R, G, B] (0-255), ex.: [255, 165, 0] = laranja
    """
    if key not in paths:
        raise KeyError(f"Caminho {key} nao existe. Chaves disponiveis: {list(paths)}")
    if len(rgb) != 3 or not all(0 <= int(c) <= 255 for c in rgb):
        raise ValueError("rgb deve ser uma lista [R, G, B] com valores de 0 a 255")

    times = paths[key]  # {"_100_": {"delay": ..., "time": ...}, ...}
    color = "#{:02x}{:02x}{:02x}".format(*(int(c) for c in rgb))

    # aceita no ja pintado antes (style/fillcolor e Delay/Time ja escritos) para poder repintar
    pat_node = re.compile(r'^(c\d+) \[ shape=record,(?: style=filled, fillcolor="[^"]*",)? label="(.*)" \];$')
    pat_name = re.compile(r"\|(_\d+_)\\n(\w+)(?:\\n[^|]*)?\|")
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
                val = times[cell]
                if isinstance(val, dict):
                    metrics = f"Delay: {val['delay']:.5f}\\nTime: {val['time']:.5f}"
                elif isinstance(val, (tuple, list)):
                    metrics = f"Delay: {val[0]:.5f}\\nTime: {val[1]:.5f}"
                else:
                    metrics = f"{val:.5f}"
                label = pat_name.sub(
                    lambda _: f"|{cell}\\n{ctype}\\n{metrics}|", label, count=1)
                line = (f'{node} [ shape=record, style=filled, fillcolor="{color}", '
                        f'label="{label}" ];')
        new_lines.append(line)

    missing = set(times) - found
    if missing:
        print(f"Aviso: celulas do caminho {key} nao encontradas no dot: {sorted(missing)}")

    with open(dot_file, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")