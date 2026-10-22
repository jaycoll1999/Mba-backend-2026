from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.question import QuestionExamPublic

class QuizStartDailyRequest(BaseModel):
    date_str: Optional[str] = None  # YYYY-MM-DD, defaults to today's UTC date

class QuizStartSubjectRequest(BaseModel):
    subject_id: int

class QuizStartUnitRequest(BaseModel):
    unit_id: int

class QuizSessionResponse(BaseModel):
    attempt_id: int
    quiz_type: str
    subject_id: Optional[int] = None
    unit_id: Optional[int] = None
    total_questions: int = 30
    started_at: datetime
    questions: List[QuestionExamPublic]

class QuizAnswerInput(BaseModel):
    question_id: int
    selected_option: Optional[str] = None

class QuizSubmitRequest(BaseModel):
    attempt_id: int
    answers: List[QuizAnswerInput]
    time_taken_seconds: int = Field(0, ge=0)

class QuizResponseReview(BaseModel):
    question_id: int
    question_text: str
    difficulty: str
    options: List[str]
    selected_option: Optional[str] = None
    correct_answer: str
    explanation: Optional[str] = None
    is_correct: bool
    marks_awarded: float

class QuizResultResponse(BaseModel):
    attempt_id: int
    quiz_type: str
    subject_id: Optional[int] = None
    unit_id: Optional[int] = None
    score: float
    total_marks: float = 30.0
    percentage: float
    is_submitted: bool
    started_at: datetime
    completed_at: datetime
    time_taken_seconds: int
    streak_days: int
    responses: List[QuizResponseReview]

class QuizAttemptSummary(BaseModel):
    id: int
    quiz_type: str
    subject_name: Optional[str] = None
    unit_title: Optional[str] = None
    score: Optional[float] = None
    total_questions: int = 30
    percentage: Optional[float] = None
    is_submitted: bool
    date_str: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
