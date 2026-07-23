from pathlib import Path

def print_tree(directory, prefix=""):
    # Ordner und Dateien, die ignoriert werden sollen (halte die Liste sauber)
    ignore = {'.git', '__pycache__', 'venv', '.idea', '.vscode', 'data', 'get_tree.py'}
    
    path = Path(directory)
    
    # Elemente sammeln und sortieren (Ordner zuerst, dann Dateien alphabetisch)
    items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
    items = [item for item in items if item.name not in ignore]
    
    for i, item in enumerate(items):
        is_last = (i == len(items) - 1)
        connector = "└── " if is_last else "├── "
        
        if item.is_dir():
            print(f"{prefix}{connector}📂 {item.name}/")
            extension = "    " if is_last else "│   "
            print_tree(item, prefix + extension)
        else:
            print(f"{prefix}{connector}📜 {item.name}")

# Passe den Namen deines Hauptordners hier an
print("📦 mosaic-AI/  (Hauptordner)")
print_tree(".")