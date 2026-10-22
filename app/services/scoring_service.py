from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.question import Question
from app.models.quiz import QuizAttempt, QuizResponse
from app.schemas.quiz import QuizSubmitRequest, QuizResultResponse, QuizResponseReview

def _is_option_match(selected: str, correct: str, options: list) -> bool:
    """
    Check if the user's selected option matches the correct answer.
    Supports either exact text match or letter match ('A', 'B', 'C', 'D').
    """
    if not selected or not correct:
        return False
        
    s_clean = selected.strip()
    c_clean = correct.strip()
    
    # 1. Direct match (case-insensitive)
    if s_clean.lower() == c_clean.lower():
        return True
        
    # 2. Check if correct is an index letter 'A', 'B', 'C', 'D'
    letter_indices = {"A": 0, "B": 1, "C": 2, "D": 3}
    if c_clean.upper() in letter_indices and options:
        idx = letter_indices[c_clean.upper()]
        if 0 <= idx < len(options):
            if s_clean.lower() == options[idx].strip().lower():
                return True
                
    # 3. Check if user sent 'A', 'B', 'C', 'D' but correct is full text
    if s_clean.upper() in letter_indices and options:
        idx = letter_indices[s_clean.upper()]
        if 0 <= idx < len(options):
            if options[idx].strip().lower() == c_clean.lower():
                return True
                
    return False

def update_user_streak(user: User, db: Session, today_str: str):
    """Update student daily streak based on calendar days."""
    if not user.last_active_date:
        user.streak_days = 1
        user.last_active_date = today_str
    elif user.last_active_date == today_str:
        # Already recorded activity today; streak remains unchanged
        pass
    else:
        try:
            last_date = datetime.strptime(user.last_active_date, "%Y-%m-%d").date()
            today_date = datetime.strptime(today_str, "%Y-%m-%d").date()
            if today_date - last_date == timedelta(days=1):
                # Consecutive day: increment streak
                user.streak_days += 1
            else:
                # Streak broken: reset to 1
                user.streak_days = 1
            user.last_active_date = today_str
        except Exception:
            user.streak_days = 1
            user.last_active_date = today_str


def score_quiz_submission(
    db: Session,
    user: User,
    submission: QuizSubmitRequest
) -> QuizResultResponse:
    """
    Scores a quiz attempt:
    - Rejects already-submitted attempts (HTTP 400 - prevents result manipulation).
    - Checks user ownership.
    - Evaluates each answer, awards 1 mark per correct answer (out of 30).
    - Records responses in quiz_responses table.
    - Updates user study streak.
    - Returns full question review with explanations.
    """
    attempt = db.query(QuizAttempt).filter(QuizAttempt.id == submission.attempt_id).first()
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz attempt {submission.attempt_id} not found."
        )

    if attempt.user_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to submit this quiz attempt."
        )

    # Validate that the same attempt cannot be submitted repeatedly to manipulate results
    if attempt.is_submitted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This quiz attempt has already been submitted and scored. Duplicate submissions are not allowed."
        )

    # Map answers by question_id
    answers_map: Dict[int, str] = {
        ans.question_id: ans.selected_option
        for ans in submission.answers
        if ans.selected_option is not None
    }

    # Fetch all questions submitted
    question_ids = list({ans.question_id for ans in submission.answers})
    questions = db.query(Question).filter(Question.id.in_(question_ids)).all() if question_ids else []
    question_lookup = {q.id: q for q in questions}

    total_score = 0.0
    reviews: List[QuizResponseReview] = []
    responses_to_save: List[QuizResponse] = []
    now = datetime.now(timezone.utc)

    for ans in submission.answers:
        q = question_lookup.get(ans.question_id)
        if not q:
            continue

        selected = ans.selected_option
        is_correct = _is_option_match(selected, q.correct_answer, q.options)
        marks = 1.0 if is_correct else 0.0
        total_score += marks

        # Create response record
        quiz_resp = QuizResponse(
            attempt_id=attempt.id,
            question_id=q.id,
            selected_option=selected,
            is_correct=is_correct,
            marks_awarded=marks,
            answered_at=now
        )
        responses_to_save.append(quiz_resp)

        reviews.append(
            QuizResponseReview(
                question_id=q.id,
                question_text=q.question_text,
                difficulty=q.difficulty,
                options=q.options,
                selected_option=selected,
                correct_answer=q.correct_answer,
                explanation=q.explanation,
                is_correct=is_correct,
                marks_awarded=marks
            )
        )

    # Save responses
    db.add_all(responses_to_save)

    # Update attempt
    total_marks = 30.0
    percentage = round((total_score / total_marks) * 100, 2)
    attempt.score = total_score
    attempt.percentage = percentage
    attempt.is_submitted = True
    attempt.time_taken_seconds = submission.time_taken_seconds
    attempt.completed_at = now

    # Update user streak
    today_str = now.strftime("%Y-%m-%d")
    update_user_streak(user, db, today_str)

    db.commit()
    db.refresh(attempt)
    db.refresh(user)

    return QuizResultResponse(
        attempt_id=attempt.id,
        quiz_type=attempt.quiz_type,
        subject_id=attempt.subject_id,
        unit_id=attempt.unit_id,
        score=attempt.score,
        total_marks=total_marks,
        percentage=attempt.percentage,
        is_submitted=True,
        started_at=attempt.started_at,
        completed_at=attempt.completed_at,
        time_taken_seconds=attempt.time_taken_seconds,
        streak_days=user.streak_days,
        responses=reviews
    )
