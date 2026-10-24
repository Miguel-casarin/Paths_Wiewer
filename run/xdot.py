import subprocess

def plot_graf(graf: str, dot_file):
    subprocess.run(["xdot", str(dot_file)])