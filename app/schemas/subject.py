from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class SyllabusSourceBase(BaseModel):
    university_name: str = "Autonomous / State MBA Curriculum"
    academic_year: str = "2024-2026"
    syllabus_version: str = "v1.0 (Verified)"
    source_url: Optional[str] = None
    verification_status: str = "verified"
    verified_by: Optional[str] = "Academic Board"
    notes: Optional[str] = None

class SyllabusSourceCreate(SyllabusSourceBase):
    subject_id: int

class SyllabusSourceResponse(SyllabusSourceBase):
    id: int
    subject_id: int
    verified_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SubjectBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    credits: int = 3
    semester: int = 1
    icon_name: str = "BookOpen"
    color_code: str = "blue"

class SubjectCreate(SubjectBase):
    pass

class SubjectUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    credits: Optional[int] = None
    semester: Optional[int] = None
    icon_name: Optional[str] = None
    color_code: Optional[str] = None

class SubjectResponse(SubjectBase):
    id: int
    created_at: datetime
    updated_at: datetime
    units_count: int = 0
    questions_count: int = 0
    syllabus_sources: List[SyllabusSourceResponse] = []

    class Config:
        from_attributes = True
