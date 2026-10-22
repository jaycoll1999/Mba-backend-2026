import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.question import Question, DifficultyLevel
from app.models.subject import Subject
from app.models.unit import Unit
from app.models.user import User
from app.core.dependencies import get_current_user, require_admin
from app.schemas.question import (
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    QuestionImportResult
)
from app.services.question_import import (
    import_questions_from_json,
    import_questions_from_csv
)

router = APIRouter(prefix="/questions", tags=["Question Bank"])

def _to_question_response(q: Question) -> QuestionResponse:
    return QuestionResponse(
        id=q.id,
        subject_id=q.subject_id,
        unit_id=q.unit_id,
        question_text=q.question_text,
        difficulty=q.difficulty,
        options=q.options,
        correct_answer=q.correct_answer,
        explanation=q.explanation,
        source_reference=q.source_reference,
        is_active=q.is_active,
        is_approved=q.is_approved,
        created_at=q.created_at,
        updated_at=q.updated_at
    )

@router.get("", response_model=List[QuestionResponse])
def list_questions(
    subject_id: Optional[int] = Query(None, description="Filter by subject"),
    unit_id: Optional[int] = Query(None, description="Filter by unit"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty: easy, medium, hard"),
    is_approved: Optional[bool] = Query(None, description="Filter by approval status"),
    search: Optional[str] = Query(None, description="Search question text"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List questions with filters.
    Students only see approved, active questions. Admins see all based on filter.
    """
    query = db.query(Question)

    if current_user.role != "admin":
        query = query.filter(Question.is_active == True, Question.is_approved == True)
    else:
        if is_approved is not None:
            query = query.filter(Question.is_approved == is_approved)

    if subject_id:
        query = query.filter(Question.subject_id == subject_id)
    if unit_id:
        query = query.filter(Question.unit_id == unit_id)
    if difficulty:
        query = query.filter(Question.difficulty == difficulty.lower())
    if search:
        query = query.filter(Question.question_text.ilike(f"%{search}%"))

    questions = query.order_by(Question.id.desc()).offset(offset).limit(limit).all()
    return [_to_question_response(q) for q in questions]

@router.post("", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(
    q_in: QuestionCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Create a new validated question (Admin only)."""
    subject = db.query(Subject).filter(Subject.id == q_in.subject_id).first()
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found.")

    if q_in.unit_id:
        unit = db.query(Unit).filter(Unit.id == q_in.unit_id, Unit.subject_id == q_in.subject_id).first()
        if not unit:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unit does not belong to this subject.")

    # Duplicate prevention check
    existing = (
        db.query(Question)
        .filter(
            Question.subject_id == q_in.subject_id,
            Question.question_text.ilike(q_in.question_text.strip())
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A question with identical or very similar text already exists for this subject."
        )

    new_q = Question(
        subject_id=q_in.subject_id,
        unit_id=q_in.unit_id,
        question_text=q_in.question_text.strip(),
        difficulty=q_in.difficulty.lower(),
        options_json=json.dumps(q_in.options),
        correct_answer=q_in.correct_answer.strip(),
        explanation=q_in.explanation,
        source_reference=q_in.source_reference,
        is_active=q_in.is_active,
        is_approved=q_in.is_approved,
        created_by_id=admin.id,
        approved_by_id=admin.id if q_in.is_approved else None
    )
    db.add(new_q)
    db.commit()
    db.refresh(new_q)
    return _to_question_response(new_q)

@router.get("/{question_id}", response_model=QuestionResponse)
def get_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get single question details (requires authentication)."""
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")
    return _to_question_response(q)

@router.put("/{question_id}", response_model=QuestionResponse)
def update_question(
    question_id: int,
    q_in: QuestionUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Update question details (Admin only)."""
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

    data = q_in.model_dump(exclude_unset=True)
    if "options" in data:
        data["options_json"] = json.dumps(data.pop("options"))

    for field, val in data.items():
        setattr(q, field, val)

    db.commit()
    db.refresh(q)
    return _to_question_response(q)

@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Delete a question (Admin only)."""
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")
    db.delete(q)
    db.commit()
    return None

@router.put("/{question_id}/approve", response_model=QuestionResponse)
def approve_question(
    question_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Approve an imported question for publication into active quiz pools (Admin only)."""
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")
    
    q.is_approved = True
    q.approved_by_id = admin.id
    db.commit()
    db.refresh(q)
    return _to_question_response(q)

@router.post("/import", response_model=QuestionImportResult)
def import_questions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Import questions from a validated JSON or CSV file.
    Imported questions default to is_approved=False and require admin review before being published.
    """
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file uploaded.")

    content = file.file.read().decode("utf-8")
    ext = file.filename.split(".")[-1].lower()

    if ext == "json":
        return import_questions_from_json(content, db, admin.id)
    elif ext == "csv":
        return import_questions_from_csv(content, db, admin.id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '.{ext}'. Please upload a .json or .csv file."
        )
