from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User
from app.models.question import Question
from app.models.subject import Subject
from app.models.resource import Resource
from app.models.quiz import QuizAttempt
from app.core.dependencies import require_admin
from app.schemas.question import QuestionResponse
from app.routers.questions import _to_question_response

router = APIRouter(prefix="/admin", tags=["Admin Content Management"])

class AdminStatsResponse(BaseModel):
    total_students: int
    total_subjects: int
    total_questions: int
    approved_questions: int
    pending_approval_questions: int
    total_resources: int
    total_quizzes_completed: int

class BatchApproveRequest(BaseModel):
    question_ids: List[int]

class BatchApproveResponse(BaseModel):
    approved_count: int
    failed_ids: List[int]

@router.get("/stats", response_model=AdminStatsResponse)
def get_system_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Retrieve system health and content metrics (Admin only)."""
    total_students = db.query(func.count(User.id)).filter(User.role == "student").scalar() or 0
    total_subjects = db.query(func.count(Subject.id)).scalar() or 0
    total_questions = db.query(func.count(Question.id)).scalar() or 0
    approved_questions = db.query(func.count(Question.id)).filter(Question.is_approved == True).scalar() or 0
    pending_questions = db.query(func.count(Question.id)).filter(Question.is_approved == False).scalar() or 0
    total_resources = db.query(func.count(Resource.id)).scalar() or 0
    total_attempts = db.query(func.count(QuizAttempt.id)).filter(QuizAttempt.is_submitted == True).scalar() or 0

    return AdminStatsResponse(
        total_students=total_students,
        total_subjects=total_subjects,
        total_questions=total_questions,
        approved_questions=approved_questions,
        pending_approval_questions=pending_questions,
        total_resources=total_resources,
        total_quizzes_completed=total_attempts
    )

@router.get("/pending-questions", response_model=List[QuestionResponse])
def get_pending_imported_questions(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """List questions awaiting admin verification and publication (Admin only)."""
    questions = db.query(Question).filter(Question.is_approved == False).order_by(Question.id.desc()).all()
    return [_to_question_response(q) for q in questions]

@router.post("/approve-batch", response_model=BatchApproveResponse)
def batch_approve_questions(
    req: BatchApproveRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Batch approve imported questions to publish them into the active question bank."""
    approved_count = 0
    failed_ids = []

    for q_id in req.question_ids:
        q = db.query(Question).filter(Question.id == q_id).first()
        if q:
            q.is_approved = True
            q.approved_by_id = admin.id
            approved_count += 1
        else:
            failed_ids.append(q_id)

    db.commit()
    return BatchApproveResponse(approved_count=approved_count, failed_ids=failed_ids)
