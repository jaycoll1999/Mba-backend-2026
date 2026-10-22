







import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.resource import Resource, ResourceType
from app.models.subject import Subject
from app.models.user import User
from app.core.dependencies import get_current_user, get_optional_current_user, require_admin
from app.schemas.resource import ResourceResponse
from app.services.storage_service import validate_and_save_pdf

router = APIRouter(prefix="/resources", tags=["Books, Question Papers & Solved Papers"])

def _format_file_size(size_bytes: Optional[int]) -> str:
    if not size_bytes or size_bytes <= 0:
        return "Unknown size"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"

def _to_resource_response(r: Resource) -> ResourceResponse:
    return ResourceResponse(
        id=r.id,
        title=r.title,
        resource_type=r.resource_type,
        subject_id=r.subject_id,
        subject_name=r.subject.name if r.subject else None,
        author=r.author,
        publisher=r.publisher,
        edition=r.edition,
        exam_session=r.exam_session,
        exam_month=r.exam_month,
        exam_year=r.exam_year,
        exam_pattern=r.exam_pattern,
        file_name=r.file_name,
        file_size_bytes=r.file_size_bytes,
        mime_type=r.mime_type,
        source_reference=r.source_reference,
        is_verified_solution=r.is_verified_solution,
        verification_disclaimer=r.verification_disclaimer,
        download_url=f"/api/v1/resources/{r.id}/download",
        preview_url=f"/api/v1/resources/{r.id}/preview",
        file_size_formatted=_format_file_size(r.file_size_bytes),
        pages=None,
        created_at=r.created_at
    )

@router.post("/upload", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
def upload_resource(
    title: str = Form(...),
    resource_type: str = Form(..., description="'book', 'question_paper', or 'solved_paper'"),
    subject_id: int = Form(...),
    author: Optional[str] = Form(None),
    publisher: Optional[str] = Form(None),
    edition: Optional[str] = Form(None),
    exam_session: Optional[str] = Form(None),
    exam_month: Optional[str] = Form(None),
    exam_year: Optional[int] = Form(None),
    exam_pattern: Optional[str] = Form(None),
    source_reference: Optional[str] = Form(None),
    is_verified_solution: bool = Form(False),
    verification_disclaimer: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Upload a validated PDF document (Books, Question Papers, or Solved Papers).
    Admin only. Validates PDF type and size limit <= 50MB.
    """
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found.")

    r_type = resource_type.lower().strip()
    if r_type not in [ResourceType.BOOK.value, ResourceType.QUESTION_PAPER.value, ResourceType.SOLVED_PAPER.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid resource type '{resource_type}'. Must be 'book', 'question_paper', or 'solved_paper'."
        )

    # Validate and save file securely
    subfolder = "books" if r_type == "book" else ("question_papers" if r_type == "question_paper" else "solved_papers")
    filename, stored_path, file_size = validate_and_save_pdf(file, subfolder=subfolder)

    # Set appropriate disclaimer if solved paper
    disclaimer = verification_disclaimer
    if r_type == ResourceType.SOLVED_PAPER.value and not disclaimer:
        if is_verified_solution:
            disclaimer = "Verified model solution compiled and authenticated by MBA Department faculty."
        else:
            disclaimer = "⚠️ Unverified student reference draft. Cross-verify calculations and theory before exams."

    resource = Resource(
        title=title,
        resource_type=r_type,
        subject_id=subject.id,
        author=author,
        publisher=publisher,
        edition=edition,
        exam_session=exam_session,
        exam_month=exam_month,
        exam_year=exam_year,
        exam_pattern=exam_pattern,
        file_name=filename,
        file_path=stored_path,
        file_size_bytes=file_size,
        mime_type="application/pdf",
        source_reference=source_reference or "University Official Repository",
        is_verified_solution=is_verified_solution,
        verification_disclaimer=disclaimer,
        uploaded_by_id=admin.id
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)

    return _to_resource_response(resource)

@router.get("/books", response_model=List[ResourceResponse])
def list_books(
    subject_id: Optional[int] = Query(None),
    subjectId: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """List reference textbooks and study guides."""
    sid = subject_id or subjectId
    q = db.query(Resource).filter(Resource.resource_type == ResourceType.BOOK.value)
    if sid:
        q = q.filter(Resource.subject_id == sid)
    if search:
        q = q.filter(
            (Resource.title.ilike(f"%{search}%")) |
            (Resource.author.ilike(f"%{search}%")) |
            (Resource.publisher.ilike(f"%{search}%"))
        )
    books = q.order_by(desc(Resource.id)).all()
    return [_to_resource_response(b) for b in books]

@router.get("/papers", response_model=List[ResourceResponse])
@router.get("/question-papers", response_model=List[ResourceResponse])
def list_university_question_papers(
    subject_id: Optional[int] = Query(None),
    subjectId: Optional[int] = Query(None),
    exam_year: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    exam_session: Optional[str] = Query(None),
    pattern: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """List official original university semester question papers."""
    sid = subject_id or subjectId
    yr = exam_year or year
    q = db.query(Resource).filter(Resource.resource_type == ResourceType.QUESTION_PAPER.value)
    if sid:
        q = q.filter(Resource.subject_id == sid)
    if yr:
        q = q.filter(Resource.exam_year == yr)
    if exam_session:
        q = q.filter(Resource.exam_session.ilike(exam_session))
    if pattern and pattern != "all":
        q = q.filter(Resource.exam_pattern.ilike(f"%{pattern}%"))
    if search:
        q = q.filter(Resource.title.ilike(f"%{search}%"))
    papers = q.order_by(desc(Resource.exam_year), desc(Resource.id)).all()
    return [_to_resource_response(p) for p in papers]

@router.get("/solved-papers", response_model=List[ResourceResponse])
def list_solved_papers(
    subject_id: Optional[int] = Query(None),
    subjectId: Optional[int] = Query(None),
    exam_year: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    is_verified_only: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    List solved question papers and model answer sheets.
    Kept separate from original question papers and tagged with verification status & disclaimers.
    """
    sid = subject_id or subjectId
    yr = exam_year or year
    q = db.query(Resource).filter(Resource.resource_type == ResourceType.SOLVED_PAPER.value)
    if sid:
        q = q.filter(Resource.subject_id == sid)
    if yr:
        q = q.filter(Resource.exam_year == yr)
    if is_verified_only is not None:
        q = q.filter(Resource.is_verified_solution == is_verified_only)
    if search:
        q = q.filter(Resource.title.ilike(f"%{search}%"))
    papers = q.order_by(desc(Resource.exam_year), desc(Resource.id)).all()
    return [_to_resource_response(p) for p in papers]

@router.get("/{resource_id}", response_model=ResourceResponse)
def get_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get single resource by ID."""
    res = db.query(Resource).filter(Resource.id == resource_id).first()
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found.")
    return _to_resource_response(res)

@router.get("/{resource_id}/preview")
def preview_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Inline PDF preview endpoint."""
    res = db.query(Resource).filter(Resource.id == resource_id).first()
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found.")

    if not os.path.exists(res.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource file missing on storage server.")

    return FileResponse(
        path=res.file_path,
        media_type="application/pdf",
        filename=res.file_name,
        content_disposition_type="inline"
    )

@router.get("/{resource_id}/download")
def download_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Attachment PDF download endpoint."""
    res = db.query(Resource).filter(Resource.id == resource_id).first()
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found.")

    if not os.path.exists(res.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource file missing on storage server.")

    return FileResponse(
        path=res.file_path,
        media_type="application/pdf",
        filename=res.file_name,
        content_disposition_type="attachment"
    )

@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Delete a library resource and remove its file (Admin only)."""
    res = db.query(Resource).filter(Resource.id == resource_id).first()
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found.")

    if os.path.exists(res.file_path):
        try:
            os.remove(res.file_path)
        except Exception:
            pass

    db.delete(res)
    db.commit()
    return None
