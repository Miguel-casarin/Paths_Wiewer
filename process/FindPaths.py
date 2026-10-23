def count_cell_in_step(steps_dict: dict, step: int, cell: str) -> int:
    """Busca a contagem de ocorrências de uma célula nos arrivals de um step específico."""
    # Suporta chave inteira ou string no dicionário
    step_data = steps_dict.get(step)
    if step_data is None:
        step_data = steps_dict.get(str(step))

    if not step_data:
        return 0

    arrivals_dict = step_data.get("arrivals", {})
    occurrence = 0

    for lista_arrivals in arrivals_dict.values():
        occurrence += lista_arrivals.count(cell)

    return occurrence


def previos_ocurence(steps_dict: dict, step: int, cell: str) -> int:
    """Retorna a ocorrência da célula nos arrivals do step anterior (step - 1).
    Se for o primeiro step (step <= 1), retorna 0."""
    if step <= 1:
        return 0

    if step == 1:
        return count_cell_in_step(steps_dict, step, cell)
    else:
        return count_cell_in_step(steps_dict, step - 1, cell)


def curence_ocurence(steps_dict: dict, step: int, cell: str) -> int:
    """Retorna a ocorrência da célula nos arrivals do step atual."""
    return count_cell_in_step(steps_dict, step, cell)


# Alias para compatibilidade
current_ocurence = curence_ocurence


