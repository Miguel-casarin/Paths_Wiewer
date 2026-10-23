import re

class Read_timing:
    def __init__(self, sta_output: str):
        self.sta_output = sta_output

    def get_arrival_times(self) -> dict:
        arrivals = {}
        path_id = 0
        current_arrival = None
        inside_path = False

        for line in self.sta_output.splitlines():
            line = line.strip()

            if line.startswith("Startpoint:"):
                # salva o caminho anterior
                if current_arrival is not None:
                    arrivals[path_id] = current_arrival

                path_id += 1
                current_arrival = None
                inside_path = True

            elif "data arrival time" in line and inside_path:
                if current_arrival is None:  # pega só o primeiro
                    value = float(line.split()[0])
                    if value > 0:
                        current_arrival = value

        # salva o último caminho
        if current_arrival is not None:
            arrivals[path_id] = current_arrival

        return arrivals

    def get_cells(self) -> dict:
        pcritic_id = 0
        result = {}

        pattern_cells = re.compile(r"(_\d+_)/")

        for line in self.sta_output.splitlines():
            line = line.strip()

            if line.startswith("Startpoint"):
                pcritic_id += 1
                result[pcritic_id] = []
                continue

            match = pattern_cells.search(line)
            if match and pcritic_id > 0:
                result[pcritic_id].append(match.group(1))

        return result


    # retorna a ocorrência de um dado gate em todos os caminhos críticos do sta
    def ocurence_by_paths(self) -> dict:
        result = {}
        pattern_cells = re.compile(r"(_\d+_)/")

        for line in self.sta_output.splitlines():
            line = line.strip()

            match = pattern_cells.search(line)
            if match:
                cell_id = match.group(1)

                if cell_id not in result:
                    result[cell_id] = 0

                result[cell_id] += 1

        return result

    def get_power(self) -> float | None:
        pattern = re.compile(r"^Total\s+(?:\S+\s+){3}(\S+)", re.MULTILINE)

        match = pattern.search(self.sta_output)

        if match:
            return float(match.group(1))
        return None

    def get_all(self) -> dict:
        return {
            "power": self.get_power(),
            "arrival_times": self.get_arrival_times(),
            "cells": self.get_cells(),
            "ocurence_by_paths": self.ocurence_by_paths(),
        }
