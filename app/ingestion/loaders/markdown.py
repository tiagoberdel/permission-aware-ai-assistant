from pathlib import Path

def load_markdown(file_path: Path) -> str:
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    return content.strip()