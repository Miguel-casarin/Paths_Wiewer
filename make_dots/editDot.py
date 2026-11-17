import re 

class Edit_Dot:
    def __init__(self, dot_file):
        self.dot_file = dot_file
        
    def upsize_cells(self, cells_to_upsize: list, new_size: str = "X2"):
        for cell in cells_to_upsize:
            pat = re.compile(rf'(\|{re.escape(cell)}\\n\w+_)X\d+(?=\\n|\|)')
            self.dot_file = pat.sub(rf'\g<1>{new_size}', self.dot_file)

        return self.dot_file  
    
    def paint_cell(self, color: list, cell: str):
        color = "#{:02x}{:02x}{:02x}".format(*(int(c) for c in color))

        # aceita no ja pintado (style/fillcolor opcional) para poder repintar
        pat = re.compile(
            rf'^(c\d+) \[ shape=record,(?: style=filled, fillcolor="[^"]*",)?'
            rf'( label=".*\|{re.escape(cell)}\\n.*" \];)$',
            re.MULTILINE,
        )
        self.dot_file = pat.sub(
            rf'\g<1> [ shape=record, style=filled, fillcolor="{color}",\g<2>',
            self.dot_file,
        )

        return self.dot_file
    
    
    