from pathlib import Path

from langchain_docling.loader import DoclingLoader
from langchain_core.documents import Document


def load_documents(file_path: Path) -> list[Document]:
    loader = DoclingLoader(file_path=str(file_path))
    return loader.load()