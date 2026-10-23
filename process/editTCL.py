import re


def edit(tcl_file, pattern, new_text, flags=0):
    """Lê o arquivo, substitui a 1ª ocorrência do padrão e grava de volta."""
    with open(tcl_file, "r") as f:
        content = f.read()

    # lambda evita que o re.sub interprete barras invertidas no texto novo
    content, n = re.subn(pattern, lambda m: new_text, content, count=1, flags=flags)

    if n == 0:
        raise ValueError(f"Padrão não encontrado em {tcl_file}: {pattern}")

    with open(tcl_file, "w") as f:
        f.write(content)


def edit_list(tcl_file, cells_list):
    """Troca o conteúdo de 'set cells_list {...}'."""
    cells_str = " ".join(cells_list)
    new_cells_list = f"set cells_list {{{cells_str}}}"

    edit(tcl_file, r"set\s+cells_list\s+\{[^}]*\}", new_cells_list)

def edit_pre_sized_list(tcl_file: str, pre_sized_list: list):
    pre_str = " ".join(pre_sized_list)
    new_pre_list = f"set pre_sized_list {{{pre_str}}}"
 
    edit(tcl_file, r"set\s+pre_sized_list\s+\{[^}]*\}", new_pre_list)

def edit_step(tcl_file, step):
    """Troca o valor inicial de 'set step N' (não afeta 'set total_steps')."""
    edit(tcl_file, r"^set\s+step\s+\d+", f"set step {step}", flags=re.MULTILINE)


def paths_total(tcl_file, number_paths):
    with open(tcl_file, "r") as f:
        content = f.read()

    content = re.sub(
        r"(report_checks[^\n]*-group_count\s+)\d+", rf"\g<1>{number_paths}", content
    )

    with open(tcl_file, "w") as f:
        f.write(content)


def parse_inputs(tcl_file, inputs_list):
    inputs_str = " ".join(inputs_list)
    new_set_inputs = f"set_input_delay 0 -clock virt_clk [get_ports {{{inputs_str}}}]"

    edit(
        tcl_file,
        r"set_input_delay\s+.*?\[get_ports\s+\{.*?\}\]",
        new_set_inputs,
        flags=re.DOTALL,
    )


def parse_outputs(tcl_file, outputs_list):
    outputs_str = " ".join(outputs_list)
    new_set_outputs = f"set_output_delay 1 -clock virt_clk [get_ports {{{outputs_str}}}]"

    edit(
        tcl_file,
        r"set_output_delay\s+.*?\[get_ports\s+\{.*?\}\]",
        new_set_outputs,
        flags=re.DOTALL,
    )


def edit_verilog(tcl_file, verilog_path):
    edit(tcl_file, r"read_verilog\s+\S+", f"read_verilog {verilog_path}")


def edit_link_design(tcl_file, module_name):
    edit(tcl_file, r"link_design\s+\S+", f"link_design {module_name}")


def edit_liberty(tcl_file, lib_path):
    edit(tcl_file, r"read_liberty\s+\S+", f"read_liberty {lib_path}")


def setup_size_tcl(
    tcl_file: str,
    verilog_path: str,
    module_name: str,
    inputs_list: list,
    outputs_list: list,
    cells_list: list,
    step: int,
    lib_path: str = None,
):
    if lib_path:
        edit_liberty(tcl_file, lib_path)
    edit_verilog(tcl_file, verilog_path)
    edit_link_design(tcl_file, module_name)
    parse_inputs(tcl_file, inputs_list)
    parse_outputs(tcl_file, outputs_list)
    paths_total(tcl_file, len(outputs_list))
    edit_list(tcl_file, cells_list)
    edit_step(tcl_file, step)


def setup_parallel_tcl(
    tcl_file: str,
    verilog_path: str,
    module_name: str,
    inputs_list: list,
    outputs_list: list,
    cells_list: list,
    pre_sized_list: list,
    step: int,
    lib_path: str = None,
):
    setup_size_tcl(
        tcl_file,
        verilog_path,
        module_name,
        inputs_list,
        outputs_list,
        cells_list,
        step,
        lib_path,
    )
    edit_pre_sized_list(tcl_file, pre_sized_list)