"""
文档 Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class DocumentBase(BaseModel):
    original_name: str
    file_type: str
    file_size: int


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    status: Optional[str] = None
    parsed_text: Optional[str] = None
    chunk_count: Optional[int] = None
    entity_count: Optional[int] = None
    relation_count: Optional[int] = None


class DocumentInDB(DocumentBase):
    id: str
    filename: str
    file_path: str
    status: str
    parsed_text: Optional[str] = None
    chunk_count: Optional[int] = None
    entity_count: Optional[int] = None
    relation_count: Optional[int] = None
    uploaded_by: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class Document(DocumentInDB):
    pass


class DocumentListResponse(BaseModel):
    items: List[Document]
    total: int
    page: int
    page_size: int


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    status: str
    message: str
