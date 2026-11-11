import os
import shutil
from pathlib import Path

def clear_temp():
    temp_dir = Path("./temp")
    
    if not temp_dir.exists() or not temp_dir.is_dir():
        print(f"Diretório {temp_dir} não encontrado.")
        return

    count = 0
    for item in temp_dir.iterdir():
        if item.name == ".gitkeep":
            continue
            
        try:
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
            count += 1
        except Exception as e:
            print(f"Erro ao deletar {item}: {e}")

    print(f"Limpeza concluída! {count} itens removidos do diretório {temp_dir} (mantendo o .gitkeep).")

if __name__ == "__main__":
    clear_temp()