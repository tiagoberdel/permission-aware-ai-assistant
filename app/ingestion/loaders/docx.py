from docx import Document
from pathlib import Path

def load_docx(file_path: Path) -> str:
    with open(file_path, "rb") as file:
        doc = Document(file)

        paragraphs = []

        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()

            if text:
                paragraphs.append(text)

    return "\n".join(paragraphs).strip()