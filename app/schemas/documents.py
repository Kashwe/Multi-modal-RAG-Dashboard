from typing import List
from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    doc_id: str
    filename: str
    chunks: int
    session_id: str


class DocumentListItem(BaseModel):
    doc_id: str


class DocumentListResponse(BaseModel):
    session_id: str
    doc_ids: List[str]
