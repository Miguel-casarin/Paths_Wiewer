def particion_list(cells_to_upsize: list, number_threads: int) -> list:
    total_cells = len(cells_to_upsize)

    if number_threads < 1:
        raise ValueError("Number of threads too small")
    if total_cells < number_threads:
        raise ValueError("Total cells < Threads to run")
    
    parts = total_cells // number_threads
    particion_idexs = []

    for i in range(number_threads):
        s = i * parts
        f = total_cells if i == number_threads - 1 else s + parts
        particion_idexs.append((s, f))

    return particion_idexs


def starter_steps(number_threads: int, cells_to_upsize: list) -> list:
    particions = particion_list(cells_to_upsize, number_threads)
    return [s + 1 for s, _ in particions]

def define_threads(number_threads: int, cells_to_upsize: list) -> int:
    if number_threads < 1:
        raise ValueError("number_threads deve ser >= 1")

    return min(number_threads, len(cells_to_upsize))

