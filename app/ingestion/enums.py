from enum import StrEnum

class Sensitivity(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"

class DocumentFormat(StrEnum):
    PDF = "pdf"
    DOCX = "docx"
    MARKDOWN = "md"

class DocumentLanguage(StrEnum):
    ES = "es"
    EN = "en"

class DocumentArea(StrEnum):
    GENERAL = "general"
    SALES = "sales"
    FINANCE = "finance"
    HR = "hr"
    MANAGEMENT = "management"