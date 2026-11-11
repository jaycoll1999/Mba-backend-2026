import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.question import Question, DifficultyLevel
from app.models.quiz import QuizAttempt, QuizResponse, QuizType
from app.models.subject import Subject
from app.models.unit import Unit

def get_recent_attempted_question_ids(db: Session, user_id: int, days_lookback: int = 3) -> set:
    """Find question IDs attempted by the user in the last N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_lookback)
    recent_responses = (
        db.query(QuizResponse.question_id)
        .join(QuizAttempt, QuizResponse.attempt_id == QuizAttempt.id)
        .filter(QuizAttempt.user_id == user_id)
        .filter(QuizAttempt.started_at >= cutoff)
        .all()
    )
    return {r[0] for r in recent_responses}

def _select_questions_for_difficulty(
    questions_pool: List[Question],
    required_count: int,
    difficulty: str,
    recent_ids: set,
    seed_str: str,
    scope_name: str = "Question Bank"
) -> List[Question]:
    """
    Selects exactly required_count questions for the specified difficulty.
    - Avoids questions in recent_ids if pool permits.
    - Uses deterministic pseudo-random ranking based on seed_str.
    - Raises HTTPException if pool has fewer than required_count.
    - Never invents fake questions.
    """
    if len(questions_pool) < required_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Insufficient questions in {scope_name} for difficulty '{difficulty}'. "
                f"Required exactly {required_count}, but only {len(questions_pool)} active, approved questions available."
            )
        )

    # Split into fresh vs recently attempted
    fresh_questions = [q for q in questions_pool if q.id not in recent_ids]
    
    # If fresh questions satisfy the count, select from fresh pool; otherwise use entire pool
    candidate_pool = fresh_questions if len(fresh_questions) >= required_count else questions_pool

    # Deterministic sorting function based on seed + question ID
    def sort_key(q: Question) -> str:
        return hashlib.sha256(f"{seed_str}_{difficulty}_{q.id}".encode("utf-8")).hexdigest()

    sorted_candidates = sorted(candidate_pool, key=sort_key)
    return sorted_candidates[:required_count]


def generate_daily_quiz(db: Session, user: User, date_str: Optional[str] = None) -> Tuple[QuizAttempt, List[Question]]:
    """
    Generate a 30-question daily quiz:
    - Exactly 10 Easy, 10 Medium, 10 Hard.
    - Deterministic selection based on user_id and date_str.
    - Avoids repeats from recent 3 days when pool allows.
    - Reuses existing unsubmitted daily quiz attempt for the day if one was already started.
    """
    if not date_str:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Check if active unsubmitted daily attempt already exists for today
    existing_attempt = (
        db.query(QuizAttempt)
        .filter(
            QuizAttempt.user_id == user.id,
            QuizAttempt.quiz_type == QuizType.DAILY.value,
            QuizAttempt.date_str == date_str,
            QuizAttempt.is_submitted == False
        )
        .first()
    )

    seed_str = f"daily_{user.id}_{date_str}"
    recent_ids = get_recent_attempted_question_ids(db, user.id, days_lookback=3)

    # Query active, approved questions per difficulty
    easy_pool = (
        db.query(Question)
        .filter(Question.is_active == True, Question.is_approved == True, Question.difficulty == DifficultyLevel.EASY.value)
        .all()
    )
    medium_pool = (
        db.query(Question)
        .filter(Question.is_active == True, Question.is_approved == True, Question.difficulty == DifficultyLevel.MEDIUM.value)
        .all()
    )
    hard_pool = (
        db.query(Question)
        .filter(Question.is_active == True, Question.is_approved == True, Question.difficulty == DifficultyLevel.HARD.value)
        .all()
    )

    selected_easy = _select_questions_for_difficulty(easy_pool, 10, "easy", recent_ids, seed_str, "Daily Question Bank")
    selected_medium = _select_questions_for_difficulty(medium_pool, 10, "medium", recent_ids, seed_str, "Daily Question Bank")
    selected_hard = _select_questions_for_difficulty(hard_pool, 10, "hard", recent_ids, seed_str, "Daily Question Bank")

    all_selected = selected_easy + selected_medium + selected_hard

    # Deterministic interleave / shuffle so user doesn't just see easy then medium then hard in blocks
    all_selected = sorted(
        all_selected,
        key=lambda q: hashlib.sha256(f"{seed_str}_order_{q.id}".encode("utf-8")).hexdigest()
    )

    if existing_attempt:
        return existing_attempt, all_selected

    # Create new attempt
    attempt = QuizAttempt(
        user_id=user.id,
        quiz_type=QuizType.DAILY.value,
        total_questions=30,
        date_str=date_str,
        is_submitted=False,
        started_at=datetime.now(timezone.utc)
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return attempt, all_selected


def _collect_unit_exam_pool(db: Session, unit: Unit, difficulty: str) -> List[Question]:
    """Collect questions for unit exam, prioritizing selected unit, then subject, then general bank."""
    unit_qs = (
        db.query(Question)
        .filter(
            Question.unit_id == unit.id,
            Question.is_active == True,
            Question.is_approved == True,
            Question.difficulty == difficulty
        )
        .all()
    )

    needed = 10 - len(unit_qs)
    if needed > 0 and unit.subject_id:
        existing_ids = {q.id for q in unit_qs}
        subject_qs = (
            db.query(Question)
            .filter(
                Question.subject_id == unit.subject_id,
                Question.unit_id != unit.id,
                Question.is_active == True,
                Question.is_approved == True,
                Question.difficulty == difficulty
            )
            .all()
        )
        unit_qs.extend([q for q in subject_qs if q.id not in existing_ids])

    needed = 10 - len(unit_qs)
    if needed > 0:
        existing_ids = {q.id for q in unit_qs}
        general_qs = (
            db.query(Question)
            .filter(
                Question.is_active == True,
                Question.is_approved == True,
                Question.difficulty == difficulty
            )
            .all()
        )
        unit_qs.extend([q for q in general_qs if q.id not in existing_ids])

    return unit_qs


def _collect_subject_exam_pool(db: Session, subject: Subject, difficulty: str) -> List[Question]:
    """Collect questions for subject exam, prioritizing subject, then general bank."""
    subject_qs = (
        db.query(Question)
        .filter(
            Question.subject_id == subject.id,
            Question.is_active == True,
            Question.is_approved == True,
            Question.difficulty == difficulty
        )
        .all()
    )
    needed = 10 - len(subject_qs)
    if needed > 0:
        existing_ids = {q.id for q in subject_qs}
        general_qs = (
            db.query(Question)
            .filter(
                Question.is_active == True,
                Question.is_approved == True,
                Question.difficulty == difficulty
            )
            .all()
        )
        subject_qs.extend([q for q in general_qs if q.id not in existing_ids])
    return subject_qs


def generate_unit_exam(db: Session, user: User, unit_id: int) -> Tuple[QuizAttempt, List[Question]]:
    """
    Generate a 30-question Unit Exam for a selected unit:
    - Exactly 10 Easy, 10 Medium, 10 Hard.
    - Prioritizes questions from the chosen unit, supplemented by the subject pool.
    """
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unit with ID {unit_id} not found.")

    seed_str = f"unit_{user.id}_{unit_id}_{datetime.now(timezone.utc).strftime('%Y-%m-%d-%H%M')}"
    recent_ids = get_recent_attempted_question_ids(db, user.id, days_lookback=2)

    easy_pool = _collect_unit_exam_pool(db, unit, DifficultyLevel.EASY.value)
    medium_pool = _collect_unit_exam_pool(db, unit, DifficultyLevel.MEDIUM.value)
    hard_pool = _collect_unit_exam_pool(db, unit, DifficultyLevel.HARD.value)

    scope_name = f"Unit '{unit.title}'"
    selected_easy = _select_questions_for_difficulty(easy_pool, 10, "easy", recent_ids, seed_str, scope_name)
    selected_medium = _select_questions_for_difficulty(medium_pool, 10, "medium", recent_ids, seed_str, scope_name)
    selected_hard = _select_questions_for_difficulty(hard_pool, 10, "hard", recent_ids, seed_str, scope_name)

    all_selected = selected_easy + selected_medium + selected_hard
    all_selected = sorted(
        all_selected,
        key=lambda q: hashlib.sha256(f"{seed_str}_order_{q.id}".encode("utf-8")).hexdigest()
    )

    attempt = QuizAttempt(
        user_id=user.id,
        quiz_type=QuizType.UNIT.value,
        subject_id=unit.subject_id,
        unit_id=unit.id,
        total_questions=30,
        is_submitted=False,
        started_at=datetime.now(timezone.utc)
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return attempt, all_selected


def generate_subject_exam(db: Session, user: User, subject_id: int) -> Tuple[QuizAttempt, List[Question]]:
    """
    Generate a 30-question Subject Exam for a selected subject:
    - Exactly 10 Easy, 10 Medium, 10 Hard.
    - Prioritizes questions from the chosen subject, supplemented by bank if needed.
    """
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Subject with ID {subject_id} not found.")

    seed_str = f"subject_{user.id}_{subject_id}_{datetime.now(timezone.utc).strftime('%Y-%m-%d-%H%M')}"
    recent_ids = get_recent_attempted_question_ids(db, user.id, days_lookback=2)

    easy_pool = _collect_subject_exam_pool(db, subject, DifficultyLevel.EASY.value)
    medium_pool = _collect_subject_exam_pool(db, subject, DifficultyLevel.MEDIUM.value)
    hard_pool = _collect_subject_exam_pool(db, subject, DifficultyLevel.HARD.value)

    scope_name = f"Subject '{subject.name}'"
    selected_easy = _select_questions_for_difficulty(easy_pool, 10, "easy", recent_ids, seed_str, scope_name)
    selected_medium = _select_questions_for_difficulty(medium_pool, 10, "medium", recent_ids, seed_str, scope_name)
    selected_hard = _select_questions_for_difficulty(hard_pool, 10, "hard", recent_ids, seed_str, scope_name)

    all_selected = selected_easy + selected_medium + selected_hard
    all_selected = sorted(
        all_selected,
        key=lambda q: hashlib.sha256(f"{seed_str}_order_{q.id}".encode("utf-8")).hexdigest()
    )

    attempt = QuizAttempt(
        user_id=user.id,
        quiz_type=QuizType.SUBJECT.value,
        subject_id=subject.id,
        total_questions=30,
        is_submitted=False,
        started_at=datetime.now(timezone.utc)
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return attempt, all_selected

