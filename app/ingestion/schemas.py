from datetime import date

from pydantic import BaseModel, Field

from app.roles import RoleName
from app.ingestion.enums import (
    DocumentLanguage,
    Sensitivity,
    DocumentFormat,
    DocumentArea,
)

class FileMetadataSchema(BaseModel):
    language: DocumentLanguage
    path: str = Field(min_length=1)
    format: DocumentFormat


class DocumentMetadataSchema(BaseModel):
    document_id: str
    title: str
    titles: dict[DocumentLanguage, str]
    area: DocumentArea
    sensitivity: Sensitivity
    allowed_roles: list[RoleName]
    public_access: bool = False
    owner: str
    created_at: date
    original_language: DocumentLanguage
    translations: list[DocumentLanguage]
    files: list[FileMetadataSchema]