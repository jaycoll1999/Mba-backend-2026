from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.reminder import ReminderPreference
from app.models.user import User
from app.core.dependencies import get_current_user
from app.schemas.reminder import (
    ReminderPreferenceUpdate,
    ReminderPreferenceResponse,
    ReminderTriggerResponse
)
from app.services.notification_service import send_study_reminder

router = APIRouter(prefix="/reminders", tags=["Reminder Preferences"])

@router.get("/preference", response_model=ReminderPreferenceResponse)
@router.get("/settings", response_model=ReminderPreferenceResponse)
def get_user_reminder_preference(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve reminder preferences for the authenticated student."""
    pref = db.query(ReminderPreference).filter(ReminderPreference.user_id == current_user.id).first()
    if not pref:
        pref = ReminderPreference(
            user_id=current_user.id,
            reminder_time="09:00",
            timezone="Asia/Kolkata",
            is_enabled=True,
            notification_channel="in_app"
        )
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref

@router.put("/preference", response_model=ReminderPreferenceResponse)
@router.put("/settings", response_model=ReminderPreferenceResponse)
def update_user_reminder_preference(
    pref_in: ReminderPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update preferred daily practice reminder time, timezone and delivery channel."""
    pref = db.query(ReminderPreference).filter(ReminderPreference.user_id == current_user.id).first()
    if not pref:
        pref = ReminderPreference(user_id=current_user.id)
        db.add(pref)

    pref.reminder_time = pref_in.reminder_time
    pref.timezone = pref_in.timezone
    pref.is_enabled = pref_in.is_enabled
    pref.notification_channel = pref_in.notification_channel
    pref.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(pref)
    return pref

@router.post("/test-trigger", response_model=ReminderTriggerResponse)
def trigger_test_reminder(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Test trigger the reminder notification.
    Strict rule: Only claims delivery if confirmed by the notification provider.
    """
    pref = db.query(ReminderPreference).filter(ReminderPreference.user_id == current_user.id).first()
    if not pref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder preference not found.")

    delivered, status_label, provider_msg = send_study_reminder(pref, current_user, db)

    return ReminderTriggerResponse(
        success=delivered,
        status=status_label,
        provider_message=provider_msg,
        delivered=delivered,
        timestamp=datetime.now(timezone.utc)
    )
