import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from app.database import Base

class ResourceType(str, enum.Enum):
    BOOK = "book"
    QUESTION_PAPER = "question_paper"
    SOLVED_PAPER = "solved_paper"

class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    resource_type = Column(String(50), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Book-specific metadata
    author = Column(String(255), nullable=True)
    publisher = Column(String(255), nullable=True)
    edition = Column(String(100), nullable=True)
    
    # Paper-specific metadata
    exam_session = Column(String(50), nullable=True)  # Summer / Winter / End-Term
    exam_month = Column(String(50), nullable=True)    # December / May
    exam_year = Column(Integer, nullable=True)        # 2024, 2023
    exam_pattern = Column(String(100), nullable=True) # Autonomous 2024 / CBCS
    
    # File storage
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(BigInteger, default=0, nullable=False)
    mime_type = Column(String(100), default="application/pdf", nullable=False)
    
    # Provenance and verification
    source_reference = Column(String(255), nullable=True)
    is_verified_solution = Column(Boolean, default=False, nullable=False)
    verification_disclaimer = Column(
        Text,
        default="Student reference solution prepared by faculty. Cross-check with university evaluation guidelines.",
        nullable=True
    )
    
    uploaded_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    subject = relationship("Subject", back_populates="resources")
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_id])
