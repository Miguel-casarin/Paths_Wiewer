import re

class Get_IO:
    def __init__(self, file):
        self.file = file
        

    def verilog_module(self):
        
        with open(self.file, "r") as f:
            content = f.read()
            module_name = re.search(r"^\s*module\s+(\w+)", content, re.MULTILINE)

            if module_name:
                print(f"Find module {module_name.group(1)} from {self.file}")
                return module_name.group(1)
            
            else:
                return None 

    def get_inputs(self):

        inputs_list = []

        with open(self.file, "r") as f:
            for line in f:
                line = line.strip()
                cat_str = re.match(r'input\s+(\w+);', line)
                
                if cat_str:
                    print(f"Input {cat_str.group(1)} from file {self.file} add to list")

                    inputs_list.append(cat_str.group(1))
                
        return inputs_list   

    def get_outputs(self):

        outputs_list = []

        with open(self.file, "r") as f:
            for line in f:
                line = line.strip()
                cat_str = re.match(r'output\s+(\w+);', line)

                if cat_str:
                    print(f"Output {cat_str.group(1)} from {self.file} add to list")

                    outputs_list.append(cat_str.group(1)) 
                    
        return outputs_list  
    
    

class Gates_info:
    
    def __init__(self, file):
        self.file = file
        

    # nome que o yosys deu as células
    def get_cells_ids(self) -> list:
            
            gates_id = []
    
            with open(self.file, "r") as f:
                for line in f:
                    line = line.strip()
                    
                    cat_str = re.match(r'\w+_X\d+\s+(_\d+_)\s*\(', line)
    
                    if cat_str:
                        gates_id.append(cat_str.group(1))
                
                return gates_id
            
    def logic_cells_type(self) -> list:

        logic_type_list = []

        regex = re.compile(r"\b([A-Z0-9]+)_X\d+\b")

        with open(self.file, "r") as f:
            for line in f:
                line = line.strip()

                match = regex.search(line)

                if match:
                    logic_type_list.append(match.group(1))

        return logic_type_list

       

