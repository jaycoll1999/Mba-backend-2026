from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class ReminderPreference(Base):
    __tablename__ = "reminder_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    reminder_time = Column(String(10), default="09:00", nullable=False)  # HH:MM 24hr format
    timezone = Column(String(50), default="Asia/Kolkata", nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    notification_channel = Column(String(50), default="in_app", nullable=False)  # email, push, in_app
    
    # Delivery verification tracking
    last_notified_at = Column(DateTime, nullable=True)
    last_delivery_status = Column(String(50), default="never_sent", nullable=False)  # delivered, provider_confirmed, failed, provider_pending
    delivery_confirmation_code = Column(String(255), nullable=True)
    delivery_log = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="reminder_preference")
