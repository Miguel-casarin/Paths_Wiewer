class Netlist_and_topology:

    def __init__(self):
        self.nets_and_topology = {}

    def add_values(self, key) -> None:
        self.nets_and_topology[key] = {
            "LOGIC-TYPE": "",
            "FANIN": 0,
            "FANOUT": 0,
            "LOGIC-LEVEL": 0,
            "DEEP": 0,
            "Cones_ocurrence": 0
        }

class Save_features(Netlist_and_topology):

    def __init__(self):
        super().__init__()

    def fild_dictionary(self, cells_id_list: list, logic_type_list: list) -> None:
        for key, logic_type in zip(cells_id_list, logic_type_list):
            self.add_values(key)
            self.nets_and_topology[key]["LOGIC-TYPE"] = logic_type

    def ad_fanin(self, key: str, fain: int) -> None:
        self.nets_and_topology[key]["FANIN"] = fain

    def ad_fanout(self, key: str, faount: int) -> None:
        self.nets_and_topology[key]["FANOUT"] = faount

    def ad_paths_occurrence(self, key: str, occurrence: int) -> None:
        self.nets_and_topology[key]["PATHS-OCURENCE"] = occurrence

    def ad_logic_level(self, key: int, logic_level: int) -> None:
        self.nets_and_topology[key]["LOGIC-LEVEL"] = logic_level

    def ad_deep(self, key: int, deep: int) -> None:
        self.nets_and_topology[key]["DEEP"] = deep

    def ad_cone(self, key: int, cones: int) -> None:
        self.nets_and_topology[key]["Cones_ocurrence"] = cones
    