from pathlib import Path
from pypdf import PdfReader

def load_pdf(file_path: Path) -> str:
    with open(file_path, "rb") as file:
        reader = PdfReader(file)

        pages = []

        for page in reader.pages:
            text = page.extract_text()

            if text:
                pages.append(text)

    return "\n".join(pages).strip()