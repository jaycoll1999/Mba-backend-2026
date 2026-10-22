from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.subject import Subject, SyllabusSource
from app.models.unit import Unit
from app.models.question import Question
from app.models.user import User
from app.core.dependencies import get_current_user, get_optional_current_user, require_admin
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse, SyllabusSourceCreate, SyllabusSourceResponse
from app.schemas.unit import UnitCreate, UnitUpdate, UnitResponse

router = APIRouter(prefix="/subjects", tags=["Subjects & Syllabus"])

def _populate_subject_counts(db: Session, subject: Subject) -> SubjectResponse:
    units_count = db.query(func.count(Unit.id)).filter(Unit.subject_id == subject.id).scalar() or 0
    questions_count = db.query(func.count(Question.id)).filter(Question.subject_id == subject.id, Question.is_active == True, Question.is_approved == True).scalar() or 0
    
    resp = SubjectResponse.model_validate(subject)
    resp.units_count = units_count
    resp.questions_count = questions_count
    return resp

@router.get("", response_model=List[SubjectResponse])
def list_subjects(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """List all subjects with unit count and approved question count."""
    subjects = db.query(Subject).order_by(Subject.id).all()
    return [_populate_subject_counts(db, s) for s in subjects]

@router.post("", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
def create_subject(
    subject_in: SubjectCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Create a new subject (Admin only)."""
    existing = db.query(Subject).filter(
        (Subject.code == subject_in.code) | (Subject.name == subject_in.name)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Subject with code '{subject_in.code}' or name '{subject_in.name}' already exists."
        )

    new_subject = Subject(**subject_in.model_dump())
    db.add(new_subject)
    db.commit()
    db.refresh(new_subject)
    return _populate_subject_counts(db, new_subject)

@router.get("/{subject_id}", response_model=SubjectResponse)
def get_subject_detail(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get subject details by ID."""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found.")
    return _populate_subject_counts(db, subject)

@router.put("/{subject_id}", response_model=SubjectResponse)
def update_subject(
    subject_id: int,
    subject_in: SubjectUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Update subject information (Admin only)."""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found.")

    for field, val in subject_in.model_dump(exclude_unset=True).items():
        setattr(subject, field, val)

    db.commit()
    db.refresh(subject)
    return _populate_subject_counts(db, subject)

@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Delete a subject and all associated units and questions (Admin only)."""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found.")
    db.delete(subject)
    db.commit()
    return None

# UNITS UNDER SUBJECT
@router.get("/{subject_id}/units", response_model=List[UnitResponse])
def list_units_for_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """List all official verified units for a subject."""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found.")

    units = db.query(Unit).filter(Unit.subject_id == subject_id).order_by(Unit.unit_number).all()
    results = []
    for u in units:
        q_count = db.query(func.count(Question.id)).filter(
            Question.unit_id == u.id, Question.is_active == True, Question.is_approved == True
        ).scalar() or 0
        resp = UnitResponse.model_validate(u)
        resp.questions_count = q_count
        results.append(resp)
    return results

@router.post("/{subject_id}/units", response_model=UnitResponse, status_code=status.HTTP_201_CREATED)
def create_unit_for_subject(
    subject_id: int,
    unit_in: UnitCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Add an official unit under a subject (Admin only)."""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found.")

    existing = db.query(Unit).filter(
        Unit.subject_id == subject_id,
        (Unit.unit_number == unit_in.unit_number) | (Unit.title == unit_in.title)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unit with number {unit_in.unit_number} or title '{unit_in.title}' already exists for this subject."
        )

    new_unit = Unit(**unit_in.model_dump())
    new_unit.subject_id = subject_id
    db.add(new_unit)
    db.commit()
    db.refresh(new_unit)

    resp = UnitResponse.model_validate(new_unit)
    resp.questions_count = 0
    return resp

# SYLLABUS SOURCES
@router.get("/{subject_id}/syllabus-sources", response_model=List[SyllabusSourceResponse])
def get_subject_syllabus_sources(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get verified syllabus provenance and official university sources for a subject."""
    return db.query(SyllabusSource).filter(SyllabusSource.subject_id == subject_id).all()

@router.post("/{subject_id}/syllabus-sources", response_model=SyllabusSourceResponse, status_code=status.HTTP_201_CREATED)
def add_subject_syllabus_source(
    subject_id: int,
    source_in: SyllabusSourceCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Record verified syllabus source reference (Admin only)."""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found.")

    new_source = SyllabusSource(**source_in.model_dump())
    new_source.subject_id = subject_id
    db.add(new_source)
    db.commit()
    db.refresh(new_source)
    return new_source
