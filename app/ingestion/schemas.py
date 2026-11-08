from datetime import date

from pydantic import BaseModel, Field

from app.roles import RoleName
from app.ingestion.enums import (
    DocumentLanguage,
    Sensitivity,
    DocumentFormat,
    DocumentArea,
)


class DocumentSchema(BaseModel):
    document_id: str = Field(min_length=1, max_length=20)
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    language: DocumentLanguage
    allowed_roles: list[RoleName]
    sensitivity: Sensitivity
    source_format: DocumentFormat


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
    owner: str
    created_at: date
    original_language: DocumentLanguage
    translations: list[DocumentLanguage]
    files: list[FileMetadataSchema]