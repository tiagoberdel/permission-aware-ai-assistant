from functools import lru_cache
from pathlib import Path

from docling.chunking import HybridChunker
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter
from langchain_core.documents import Document
from langchain_docling.loader import DoclingLoader


@lru_cache(maxsize=1)
def get_converter() -> DocumentConverter:
    converter = DocumentConverter()
    converter.format_to_options[
        InputFormat.PDF
    ].pipeline_options.do_ocr = False

    return converter

@lru_cache(maxsize=1)
def get_chunker() -> HybridChunker:
    return HybridChunker()

def load_documents(file_path: Path) -> list[Document]:
    loader = DoclingLoader(
        file_path=str(file_path),
        converter=get_converter(),
        chunker=get_chunker(),
    )
    return loader.load()
