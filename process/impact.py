def arrival_impact(dim_arrival: dict, base_arrival: dict) -> list:
    dif_list = []
    for key, dim_val in dim_arrival.items():
        base_val = base_arrival.get(key)
        if base_val is None and isinstance(key, int):
            base_val = base_arrival.get(str(key))
        elif base_val is None and isinstance(key, str) and key.isdigit():
            base_val = base_arrival.get(int(key))

        if base_val is not None:
            dif_list.append(dim_val - base_val)
    return dif_list


def arrival_impact_pct(dim_arrival: dict, base_arrival: dict) -> list:
    pct_list = []
    for key, dim_val in dim_arrival.items():
        base_val = base_arrival.get(key)
        if base_val is None and isinstance(key, int):
            base_val = base_arrival.get(str(key))
        elif base_val is None and isinstance(key, str) and key.isdigit():
            base_val = base_arrival.get(int(key))

        if base_val is not None:
            pct = ((dim_val - base_val) / base_val) * 100 if base_val != 0 else 0.0
            pct_list.append(round(pct, 2))
    return pct_list


def power_impact(dim_power: float, base_power: float) -> float:
    if dim_power is not None and base_power is not None:
        return dim_power - base_power
    return 0.0


def power_impact_pct(dim_power: float, base_power: float) -> float:
    if base_power and base_power != 0 and dim_power is not None:
        pct = ((dim_power - base_power) / base_power) * 100
        return round(pct, 2)
    return float("inf") if dim_power != 0 else 0.0


def apply_step_impact(step_data: dict, base_power: float, base_arrivals: dict) -> dict:
    dim_power = step_data.get("power")
    dim_arrivals = step_data.get("arrival_times", {})

    step_data["dif_power"] = power_impact(dim_power, base_power)
    step_data["pct_power"] = power_impact_pct(dim_power, base_power)
    step_data["dif_arrival"] = arrival_impact(dim_arrivals, base_arrivals)
    step_data["pct_arrival"] = arrival_impact_pct(dim_arrivals, base_arrivals)

    return step_data


def apply_all_impacts(steps_dict: dict, base_power: float, base_arrivals: dict) -> dict:
    for step_data in steps_dict.values():
        apply_step_impact(step_data, base_power, base_arrivals)
    return steps_dict


def run_sta_and_impact(tcl_file: str, base_power: float, base_arrivals: dict) -> tuple[dict, int]:
    """Executa o OpenSTA para o arquivo TCL e calcula os impactos vs. baseline."""
    # imports locais para evitar import circular com o pacote run
    from process import readSTA
    from run import runSTA

    output = runSTA.run_sta(tcl_file)
    steps = readSTA.Read_steps(output).get_all()
    if not steps:
        raise ValueError(f"Nenhum 'STEP: N' encontrado na saída de {tcl_file}")

    apply_all_impacts(steps, base_power, base_arrivals)
    return steps, len(output.splitlines())


def run_sta_impact_and_paths(
    tcl_file: str, base_power: float, base_arrivals: dict
) -> tuple[dict, int]:
    """Executa o OpenSTA, calcula os impactos e embute em cada step os caminhos
    ({path_id: [ids das células em ordem]})."""
    from process import readSTA
    from run import runSTA

    output = runSTA.run_sta(tcl_file)
    reader = readSTA.Read_steps(output)
    steps = reader.get_all()
    if not steps:
        raise ValueError(f"Nenhum 'STEP: N' encontrado na saída de {tcl_file}")

    apply_all_impacts(steps, base_power, base_arrivals)

    for step, paths in reader.paths().items():
        steps[step]["paths"] = paths

    return steps, len(output.splitlines())