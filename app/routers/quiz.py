from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.database import get_db
from app.models.user import User
from app.models.quiz import QuizAttempt, QuizResponse, QuizType
from app.models.question import Question
from app.models.unit import Unit
from app.models.subject import Subject
from app.core.dependencies import get_current_user
from app.schemas.quiz import (
    QuizStartDailyRequest,
    QuizSessionResponse,
    QuizSubmitRequest,
    QuizResultResponse,
    QuizAttemptSummary,
    QuizResponseReview
)
from app.schemas.question import QuestionExamPublic
from app.services.quiz_service import (
    generate_daily_quiz,
    generate_unit_exam,
    generate_subject_exam
)
from app.services.scoring_service import score_quiz_submission

router = APIRouter(prefix="/quiz", tags=["Daily Quiz & Exams"])

def _format_exam_session(attempt: QuizAttempt, questions: List[Question]) -> QuizSessionResponse:
    # Notice: QuestionExamPublic omits correct_answer and explanation!
    public_questions = [
        QuestionExamPublic(
            id=q.id,
            subject_id=q.subject_id,
            unit_id=q.unit_id,
            question_text=q.question_text,
            difficulty=q.difficulty,
            options=q.options
        )
        for q in questions
    ]
    return QuizSessionResponse(
        attempt_id=attempt.id,
        quiz_type=attempt.quiz_type,
        subject_id=attempt.subject_id,
        unit_id=attempt.unit_id,
        total_questions=len(public_questions),
        started_at=attempt.started_at,
        questions=public_questions
    )

@router.get("/daily", response_model=QuizSessionResponse)
@router.post("/daily/start", response_model=QuizSessionResponse)
def start_daily_quiz(
    req: QuizStartDailyRequest = QuizStartDailyRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate or resume today's 30-question Daily Quiz.
    - Exactly 30 questions (10 Easy, 10 Medium, 10 Hard).
    - Answers are isolated and NEVER exposed in this endpoint.
    - Deterministic daily rotation.
    - Anti-repeat filtering from recent 3 days.
    """
    attempt, questions = generate_daily_quiz(db, current_user, req.date_str)
    return _format_exam_session(attempt, questions)

@router.get("/unit-exam", response_model=QuizSessionResponse)
def get_unit_exam_get(
    unit_id: Optional[str] = Query(None),
    unitId: Optional[str] = Query(None),
    subject_id: Optional[str] = Query(None),
    subjectId: Optional[str] = Query(None),
    unitNumber: Optional[int] = Query(None),
    unit_number: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """GET alias for unit exam with robust subject & unit resolution."""
    uid = None
    raw_uid = unit_id or unitId
    if raw_uid and str(raw_uid).isdigit():
        uid = int(raw_uid)

    if not uid:
        raw_sid = subject_id or subjectId
        target_subject = None
        if raw_sid:
            raw_s_str = str(raw_sid).strip()
            if raw_s_str.isdigit():
                target_subject = db.query(Subject).filter(Subject.id == int(raw_s_str)).first()
            if not target_subject:
                clean_code = raw_s_str.upper().replace("SUBJ-", "")
                target_subject = db.query(Subject).filter(
                    (func.upper(Subject.code) == clean_code) |
                    (func.upper(Subject.code).like(f"{clean_code}%"))
                ).first()

        u_num = unitNumber or unit_number
        if target_subject and u_num:
            u = db.query(Unit).filter(Unit.subject_id == target_subject.id, Unit.unit_number == int(u_num)).first()
            if u:
                uid = u.id

        if target_subject and not uid:
            u = db.query(Unit).filter(Unit.subject_id == target_subject.id).order_by(Unit.unit_number).first()
            if u:
                uid = u.id

    if not uid:
        # Default to first available unit in DB
        first_unit = db.query(Unit).order_by(Unit.id).first()
        if first_unit:
            uid = first_unit.id
        else:
            raise HTTPException(status_code=400, detail="No syllabus units available to start unit exam.")

    attempt, questions = generate_unit_exam(db, current_user, uid)
    return _format_exam_session(attempt, questions)

@router.post("/unit/{unit_id}/start", response_model=QuizSessionResponse)
def start_unit_exam(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a 30-question Unit Exam for the selected unit.
    - Exactly 10 Easy, 10 Medium, 10 Hard questions.
    """
    attempt, questions = generate_unit_exam(db, current_user, unit_id)
    return _format_exam_session(attempt, questions)

@router.get("/subject-exam", response_model=QuizSessionResponse)
def get_subject_exam_get(
    subject_id: Optional[str] = Query(None),
    subjectId: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """GET alias for subject exam with robust subject resolution."""
    raw_sid = subject_id or subjectId
    if not raw_sid:
        first_s = db.query(Subject).order_by(Subject.id).first()
        if first_s:
            sid_int = first_s.id
        else:
            raise HTTPException(status_code=400, detail="subject_id is required.")
    else:
        raw_s_str = str(raw_sid).strip()
        if raw_s_str.isdigit():
            sid_int = int(raw_s_str)
        else:
            clean_code = raw_s_str.upper().replace("SUBJ-", "")
            target_subject = db.query(Subject).filter(
                (func.upper(Subject.code) == clean_code) |
                (func.upper(Subject.code).like(f"{clean_code}%"))
            ).first()
            sid_int = target_subject.id if target_subject else None

    if not sid_int:
        raise HTTPException(status_code=404, detail="Subject not found.")

    attempt, questions = generate_subject_exam(db, current_user, sid_int)
    return _format_exam_session(attempt, questions)

@router.post("/subject/{subject_id}/start", response_model=QuizSessionResponse)
def start_subject_exam(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a 30-question Subject Exam for the selected subject.
    - Exactly 10 Easy, 10 Medium, 10 Hard questions.
    - Returns 400 validation error if subject pool has fewer than 10 questions in any difficulty tier.
    """
    attempt, questions = generate_subject_exam(db, current_user, subject_id)
    return _format_exam_session(attempt, questions)

@router.post("/submit", response_model=QuizResultResponse)
def submit_quiz_attempt(
    submission: QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit answers for scoring:
    - Scores 1 mark per correct answer (total 30 marks).
    - Prevents duplicate submissions of the same attempt.
    - Reveals correct answers and verified explanations ONLY after submission.
    - Updates daily study streak.
    """
    return score_quiz_submission(db, current_user, submission)

@router.get("/attempts", response_model=List[QuizAttemptSummary])
def list_user_attempts(
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List quiz attempts and scores for the authenticated student."""
    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == current_user.id)
        .order_by(desc(QuizAttempt.started_at))
        .offset(offset)
        .limit(limit)
        .all()
    )
    results = []
    for a in attempts:
        subj_name = a.subject.name if a.subject else ("Daily MBA Quiz" if a.quiz_type == QuizType.DAILY.value else None)
        unit_title = a.unit.title if a.unit else None
        results.append(
            QuizAttemptSummary(
                id=a.id,
                quiz_type=a.quiz_type,
                subject_name=subj_name,
                unit_title=unit_title,
                score=a.score,
                total_questions=a.total_questions,
                percentage=a.percentage,
                is_submitted=a.is_submitted,
                date_str=a.date_str,
                started_at=a.started_at,
                completed_at=a.completed_at
            )
        )
    return results

@router.get("/attempts/{attempt_id}", response_model=QuizResultResponse)
def get_attempt_details(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve full review and explanations for a completed quiz attempt."""
    attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found.")

    if attempt.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    if not attempt.is_submitted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This quiz attempt has not yet been submitted. Answers and explanations are hidden during the exam."
        )

    responses = db.query(QuizResponse).filter(QuizResponse.attempt_id == attempt.id).all()
    reviews = []
    for r in responses:
        q = r.question
        reviews.append(
            QuizResponseReview(
                question_id=q.id,
                question_text=q.question_text,
                difficulty=q.difficulty,
                options=q.options,
                selected_option=r.selected_option,
                correct_answer=q.correct_answer,
                explanation=q.explanation,
                is_correct=r.is_correct or False,
                marks_awarded=r.marks_awarded
            )
        )

    return QuizResultResponse(
        attempt_id=attempt.id,
        quiz_type=attempt.quiz_type,
        subject_id=attempt.subject_id,
        unit_id=attempt.unit_id,
        score=attempt.score or 0.0,
        total_marks=30.0,
        percentage=attempt.percentage or 0.0,
        is_submitted=attempt.is_submitted,
        started_at=attempt.started_at,
        completed_at=attempt.completed_at or attempt.started_at,
        time_taken_seconds=attempt.time_taken_seconds,
        streak_days=current_user.streak_days,
        responses=reviews
    )
