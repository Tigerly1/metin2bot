import os

def get_imports_from_file(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    imports = set()
    for line in lines:
        line = line.strip()
        if line.startswith("import") or line.startswith("from"):
            parts = line.split()
            if "import" in parts:
                module = parts[1].split('.')[0]
                imports.add(module)
            elif "from" in parts:
                module = parts[1].split('.')[0]
                imports.add(module)
    return imports

def generate_install_commands(directory, output_file):
    all_imports = set()
    for subdir, _, files in os.walk(directory):
        # Skip the yolov5 directory
        if 'yolov5' in subdir:
            continue
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(subdir, file)
                imports = get_imports_from_file(file_path)
                all_imports.update(imports)

    with open(output_file, 'w') as f:
        for module in all_imports:
            f.write(f"pip install {module}\n")

if __name__ == "__main__":
    generate_install_commands("/Users/filippilarek/Downloads/Metin2-Bot-main", "install_commands.txt")
