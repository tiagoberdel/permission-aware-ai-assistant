from pathlib import Path

from langchain_core.documents import Document

from app.ingestion.loader import load_documents
from app.ingestion.metadata import load_document_metadata

def ingest_documents(
    manifest_path: Path,
    dataset_root: Path
) -> list[Document]:

    document_metadata_list = load_document_metadata(manifest_path)
    ingested_documents = []

    for document_metadata in document_metadata_list:
        for file_metadata in document_metadata.files:
            file_path = dataset_root / file_metadata.path
            documents = load_documents(file_path)

            for document in documents:
                metadata = {
                    "document_id": document_metadata.document_id,
                    "title": document_metadata.titles[file_metadata.language],
                    "area": document_metadata.area.value,
                    "sensitivity": document_metadata.sensitivity.value,
                    "language": file_metadata.language.value,
                    "source_format": file_metadata.format.value,
                    "source_path": str(file_path),
                }

                if document_metadata.allowed_roles:
                    metadata["allowed_roles"] = [
                        role.value for role in document_metadata.allowed_roles
                    ]

                document.metadata.update(metadata)
                ingested_documents.append(document)

    return ingested_documents