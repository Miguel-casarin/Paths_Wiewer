import subprocess


def run_sta(tcl_file: str, sta_bin: str = "sta", cwd: str = None, timeout: float = None) -> str:
    result = subprocess.run(
        [sta_bin, tcl_file],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=timeout,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"STA FAILL {tcl_file} (CODE {result.returncode}):\n{result.stderr}"
        )

    return result.stdout
