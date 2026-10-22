from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case

from app.database import get_db
from app.models.user import User
from app.models.quiz import QuizAttempt, QuizResponse, QuizType
from app.models.question import Question
from app.models.subject import Subject
from app.models.unit import Unit
from app.core.dependencies import get_current_user
from app.schemas.analytics import (
    DashboardAnalytics,
    StreakInfo,
    SubjectAccuracy,
    DifficultyAccuracy,
    WeakTopic
)
from app.schemas.quiz import QuizAttemptSummary

router = APIRouter(prefix="/analytics", tags=["Progress & Analytics"])

@router.get("/dashboard", response_model=DashboardAnalytics)
def get_student_dashboard_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Computes comprehensive analytics for the student:
    - Total quizzes taken
    - Average score out of 30
    - Highest score
    - Study streak status
    - Subject-wise accuracy percentages
    - Difficulty-wise accuracy percentages
    - Weak-topic analysis with targeted study recommendations
    - Recent quiz attempt summaries
    """
    # 1. Overall stats
    submitted_attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == current_user.id, QuizAttempt.is_submitted == True)
        .all()
    )

    total_quizzes = len(submitted_attempts)
    avg_score = round(sum(a.score for a in submitted_attempts) / total_quizzes, 2) if total_quizzes > 0 else 0.0
    avg_pct = round(sum(a.percentage for a in submitted_attempts) / total_quizzes, 2) if total_quizzes > 0 else 0.0
    highest_score = max((a.score for a in submitted_attempts), default=0.0)

    # 2. Streak info
    streak_status = "Active" if current_user.streak_days > 0 else "Start a new streak today!"
    streak_info = StreakInfo(
        current_streak=current_user.streak_days,
        last_active_date=current_user.last_active_date,
        streak_status=streak_status
    )

    # 3. Subject-wise accuracy
    subject_stats = (
        db.query(
            Subject.id,
            Subject.name,
            func.count(QuizResponse.id).label("total"),
            func.sum(case((QuizResponse.is_correct == True, 1), else_=0)).label("correct")
        )
        .join(Question, Question.subject_id == Subject.id)
        .join(QuizResponse, QuizResponse.question_id == Question.id)
        .join(QuizAttempt, QuizAttempt.id == QuizResponse.attempt_id)
        .filter(QuizAttempt.user_id == current_user.id, QuizAttempt.is_submitted == True)
        .group_by(Subject.id, Subject.name)
        .all()
    )

    subject_performances = []
    for s_id, s_name, total, correct in subject_stats:
        total_val = total or 0
        correct_val = correct or 0
        pct = round((correct_val / total_val) * 100, 2) if total_val > 0 else 0.0
        subject_performances.append(
            SubjectAccuracy(
                subject_id=s_id,
                subject_name=s_name,
                total_attempted=total_val,
                total_correct=correct_val,
                accuracy_percentage=pct
            )
        )

    # 4. Difficulty-wise accuracy
    difficulty_stats = (
        db.query(
            Question.difficulty,
            func.count(QuizResponse.id).label("total"),
            func.sum(case((QuizResponse.is_correct == True, 1), else_=0)).label("correct")
        )
        .join(QuizResponse, QuizResponse.question_id == Question.id)
        .join(QuizAttempt, QuizAttempt.id == QuizResponse.attempt_id)
        .filter(QuizAttempt.user_id == current_user.id, QuizAttempt.is_submitted == True)
        .group_by(Question.difficulty)
        .all()
    )

    difficulty_performances = []
    for diff, total, correct in difficulty_stats:
        total_val = total or 0
        correct_val = correct or 0
        pct = round((correct_val / total_val) * 100, 2) if total_val > 0 else 0.0
        difficulty_performances.append(
            DifficultyAccuracy(
                difficulty=diff.capitalize(),
                total_attempted=total_val,
                total_correct=correct_val,
                accuracy_percentage=pct
            )
        )

    # 5. Weak topic analysis
    unit_stats = (
        db.query(
            Subject.id.label("subject_id"),
            Subject.name.label("subject_name"),
            Unit.id.label("unit_id"),
            Unit.title.label("unit_title"),
            func.count(QuizResponse.id).label("total"),
            func.sum(case((QuizResponse.is_correct == True, 1), else_=0)).label("correct")
        )
        .join(Question, Question.unit_id == Unit.id)
        .join(Subject, Subject.id == Unit.subject_id)
        .join(QuizResponse, QuizResponse.question_id == Question.id)
        .join(QuizAttempt, QuizAttempt.id == QuizResponse.attempt_id)
        .filter(QuizAttempt.user_id == current_user.id, QuizAttempt.is_submitted == True)
        .group_by(Subject.id, Subject.name, Unit.id, Unit.title)
        .having(func.count(QuizResponse.id) >= 2)
        .all()
    )

    weak_topics = []
    for s_id, s_name, u_id, u_title, total, correct in unit_stats:
        total_val = total or 0
        correct_val = correct or 0
        pct = round((correct_val / total_val) * 100, 2) if total_val > 0 else 0.0
        if pct < 70.0:  # Flag topics below 70% accuracy
            weak_topics.append(
                WeakTopic(
                    subject_id=s_id,
                    subject_name=s_name,
                    unit_id=u_id,
                    unit_title=u_title,
                    total_attempted=total_val,
                    accuracy_percentage=pct,
                    recommendation=f"Review Unit notes and solve Unit Exam for '{u_title}' to boost accuracy above 75%."
                )
            )

    # 6. Recent attempts
    recent_attempts_raw = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == current_user.id)
        .order_by(desc(QuizAttempt.started_at))
        .limit(10)
        .all()
    )
    recent_attempts = []
    for a in recent_attempts_raw:
        subj_name = a.subject.name if a.subject else ("Daily MBA Quiz" if a.quiz_type == QuizType.DAILY.value else None)
        unit_title = a.unit.title if a.unit else None
        recent_attempts.append(
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

    return DashboardAnalytics(
        total_quizzes_taken=total_quizzes,
        average_score=avg_score,
        average_percentage=avg_pct,
        highest_score=highest_score,
        streak=streak_info,
        subject_performances=subject_performances,
        difficulty_performances=difficulty_performances,
        weak_topics=weak_topics,
        recent_attempts=recent_attempts
    )
