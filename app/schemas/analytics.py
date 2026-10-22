from typing import List, Optional
from pydantic import BaseModel
from app.schemas.quiz import QuizAttemptSummary

class StreakInfo(BaseModel):
    current_streak: int
    last_active_date: Optional[str] = None
    streak_status: str

class SubjectAccuracy(BaseModel):
    subject_id: int
    subject_name: str
    total_attempted: int
    total_correct: int
    accuracy_percentage: float

class DifficultyAccuracy(BaseModel):
    difficulty: str
    total_attempted: int
    total_correct: int
    accuracy_percentage: float

class WeakTopic(BaseModel):
    subject_id: int
    subject_name: str
    unit_id: Optional[int] = None
    unit_title: Optional[str] = None
    total_attempted: int
    accuracy_percentage: float
    recommendation: str

class DashboardAnalytics(BaseModel):
    total_quizzes_taken: int
    average_score: float
    average_percentage: float
    highest_score: float
    streak: StreakInfo
    subject_performances: List[SubjectAccuracy]
    difficulty_performances: List[DifficultyAccuracy]
    weak_topics: List[WeakTopic]
    recent_attempts: List[QuizAttemptSummary]
