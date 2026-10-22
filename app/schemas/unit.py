from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class UnitBase(BaseModel):
    subject_id: int
    unit_number: int = Field(..., ge=1, le=10)
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    learning_objectives: Optional[str] = None
    source_reference: Optional[str] = None

class UnitCreate(UnitBase):
    pass

class UnitUpdate(BaseModel):
    subject_id: Optional[int] = None
    unit_number: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    learning_objectives: Optional[str] = None
    source_reference: Optional[str] = None

class UnitResponse(UnitBase):
    id: int
    created_at: datetime
    updated_at: datetime
    questions_count: int = 0

    class Config:
        from_attributes = True
