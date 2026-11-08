from pathlib import Path

from app.ingestion.loaders.docx import load_docx
from app.ingestion.loaders.markdown import load_markdown
from app.ingestion.loaders.pdf import load_pdf
from app.ingestion.enums import DocumentFormat

def load_document(file_path: Path, file_format: DocumentFormat) -> str:
    if file_format == DocumentFormat.DOCX:
        return load_docx(file_path)
    elif file_format == DocumentFormat.MARKDOWN:
        return load_markdown(file_path)
    elif file_format == DocumentFormat.PDF:
        return load_pdf(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_format}")