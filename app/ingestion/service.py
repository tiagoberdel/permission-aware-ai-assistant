from pathlib import Path

from app.ingestion.loaders import load_document
from app.ingestion.metadata import load_document_metadata
from app.ingestion.schemas import DocumentSchema


def ingest_documents(manifest_path: Path, dataset_root: Path) -> list[DocumentSchema]:
    document_metadata_list = load_document_metadata(manifest_path)

    ingested_documents = []

    for document_metadata in document_metadata_list:
        for file_metadata in document_metadata.files:
            file_path = dataset_root / file_metadata.path
            file_format = file_metadata.format
            content = load_document(file_path, file_format)

            ingested_documents.append(
                DocumentSchema(
                    document_id=document_metadata.document_id,
                    title=document_metadata.titles[file_metadata.language],
                    content=content,
                    language=file_metadata.language,
                    allowed_roles=document_metadata.allowed_roles,
                    sensitivity=document_metadata.sensitivity,
                    source_format=file_format,
                )
            )

    return ingested_documents
