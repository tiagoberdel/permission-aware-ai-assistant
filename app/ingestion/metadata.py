import json

from app.ingestion.schemas import DocumentMetadataSchema

def load_document_metadata(manifest_path: str) -> list[DocumentMetadataSchema]:
    with open(manifest_path, "r", encoding="utf-8") as file:
        return [
            DocumentMetadataSchema.model_validate(document)
            for document in json.load(file)
        ]