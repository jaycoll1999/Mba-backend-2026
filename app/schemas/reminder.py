from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class ReminderPreferenceUpdate(BaseModel):
    reminder_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="HH:MM format, e.g. 09:00")
    timezone: str = Field("Asia/Kolkata", min_length=2)
    is_enabled: bool = True
    notification_channel: str = Field("in_app", pattern="^(in_app|email|push)$")

class ReminderPreferenceResponse(BaseModel):
    id: int
    user_id: int
    reminder_time: str
    timezone: str
    is_enabled: bool
    notification_channel: str
    last_notified_at: Optional[datetime] = None
    last_delivery_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ReminderTriggerResponse(BaseModel):
    success: bool
    status: str
    provider_message: str
    delivered: bool
    timestamp: datetime
