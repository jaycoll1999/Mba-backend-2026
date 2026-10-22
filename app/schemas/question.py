from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class QuestionBase(BaseModel):
    subject_id: int
    unit_id: Optional[int] = None
    question_text: str = Field(..., min_length=5)
    difficulty: str = Field("medium", pattern="^(easy|medium|hard)$")
    options: List[str] = Field(..., min_length=4, max_length=4, description="Exactly 4 options")
    correct_answer: str = Field(..., min_length=1)
    explanation: Optional[str] = None
    source_reference: Optional[str] = None

    @field_validator("options")
    @classmethod
    def validate_four_options(cls, v):
        if len(v) != 4:
            raise ValueError("Each question must contain exactly 4 options.")
        if len(set(v)) != 4:
            raise ValueError("All 4 options must be unique.")
        return v

    @field_validator("correct_answer")
    @classmethod
    def validate_answer_in_options(cls, v, info):
        options = info.data.get("options")
        if options and v not in options:
            # Also allow if answer is "A", "B", "C", "D"
            if v.upper() not in ["A", "B", "C", "D"]:
                raise ValueError("Correct answer must match one of the 4 options or be 'A', 'B', 'C', 'D'.")
        return v

class QuestionCreate(QuestionBase):
    is_active: bool = True
    is_approved: bool = True

class QuestionUpdate(BaseModel):
    subject_id: Optional[int] = None
    unit_id: Optional[int] = None
    question_text: Optional[str] = None
    difficulty: Optional[str] = Field(None, pattern="^(easy|medium|hard)$")
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    source_reference: Optional[str] = None
    is_active: Optional[bool] = None
    is_approved: Optional[bool] = None

# EXAM VIEW: Never exposes correct_answer or explanation!
class QuestionExamPublic(BaseModel):
    id: int
    subject_id: int
    unit_id: Optional[int] = None
    question_text: str
    difficulty: str
    options: List[str]

    class Config:
        from_attributes = True

# ADMIN / FULL VIEW
class QuestionResponse(QuestionBase):
    id: int
    is_active: bool
    is_approved: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# IMPORT SCHEMAS
class QuestionImportItem(BaseModel):
    subject_code_or_id: Any
    unit_number_or_id: Optional[Any] = None
    question_text: str
    difficulty: str = "medium"
    options: List[str]
    correct_answer: str
    explanation: Optional[str] = None
    source_reference: Optional[str] = None

class QuestionImportResult(BaseModel):
    total_parsed: int
    imported_count: int
    duplicate_count: int
    error_count: int
    errors: List[str] = []
