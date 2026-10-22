from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    credits = Column(Integer, default=3, nullable=False)
    semester = Column(Integer, default=1, nullable=False)
    icon_name = Column(String(50), default="BookOpen", nullable=False)
    color_code = Column(String(50), default="blue", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    units = relationship("Unit", back_populates="subject", cascade="all, delete-orphan", order_by="Unit.unit_number")
    questions = relationship("Question", back_populates="subject", cascade="all, delete-orphan")
    resources = relationship("Resource", back_populates="subject", cascade="all, delete-orphan")
    syllabus_sources = relationship("SyllabusSource", back_populates="subject", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="subject")

class SyllabusSource(Base):
    __tablename__ = "syllabus_sources"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    university_name = Column(String(255), nullable=False, default="Autonomous / State MBA Curriculum")
    academic_year = Column(String(50), nullable=False, default="2024-2026")
    syllabus_version = Column(String(50), nullable=False, default="v1.0 (Verified)")
    source_url = Column(String(500), nullable=True)
    verification_status = Column(String(50), nullable=False, default="verified")  # verified, pending, unverified
    verified_by = Column(String(255), nullable=True, default="Academic Board")
    verified_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    subject = relationship("Subject", back_populates="syllabus_sources")
