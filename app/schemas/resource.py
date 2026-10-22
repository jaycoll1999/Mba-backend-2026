from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class ResourceResponse(BaseModel):
    id: int
    title: str
    resource_type: str
    subject_id: int
    subject_name: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    edition: Optional[str] = None
    exam_session: Optional[str] = None
    exam_month: Optional[str] = None
    exam_year: Optional[int] = None
    exam_pattern: Optional[str] = None
    file_name: str
    file_size_bytes: int
    mime_type: str
    source_reference: Optional[str] = None
    is_verified_solution: bool
    verification_disclaimer: Optional[str] = None
    download_url: Optional[str] = None
    preview_url: Optional[str] = None
    file_size_formatted: Optional[str] = None
    pages: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ResourceFilter(BaseModel):
    resource_type: Optional[str] = None
    subject_id: Optional[int] = None
    exam_year: Optional[int] = None
    search: Optional[str] = None
