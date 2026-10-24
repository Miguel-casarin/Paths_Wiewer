from pathlib import Path
import shutil
import json

def file_exists(directory, filename) -> bool:
    return (Path(directory) / filename).is_file()

def copy_rename(input_file: str, name_to_save: str, save_path: str):
    shutil.copy(input_file, f"{save_path}/{name_to_save}")

def save_dict_as_json(dict_to_save: str, json_to_save: str):
    with open(json_to_save, "w") as f:
        json.dump(dict_to_save, f, indent=4)

def returns_cells_steps(priority_file: str) -> list:
    with open(priority_file, "r") as file:
        priority = [line.strip() for line in file]
    return priority