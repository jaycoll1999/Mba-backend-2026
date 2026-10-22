import logging
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.database import SessionLocal
from app.models.reminder import ReminderPreference
from app.models.user import User
from app.services.notification_service import send_study_reminder

logger = logging.getLogger("mba_scheduler")

scheduler = BackgroundScheduler()

def check_and_send_scheduled_reminders():
    """
    Background job that checks active reminder preferences against current time.
    Only updates delivery confirmation if confirmed by the notification provider.
    """
    if not settings.NOTIFICATION_ENABLED:
        return

    db = SessionLocal()
    try:
        now_utc = datetime.now(timezone.utc)
        current_time_str = now_utc.strftime("%H:%M")

        active_preferences = (
            db.query(ReminderPreference)
            .join(User, User.id == ReminderPreference.user_id)
            .filter(ReminderPreference.is_enabled == True, User.is_active == True)
            .all()
        )

        for pref in active_preferences:
            user = pref.user
            # Check if reminder already sent today
            if pref.last_notified_at and pref.last_notified_at.date() == now_utc.date():
                continue

            # Compare hours and minutes
            if pref.reminder_time == current_time_str:
                send_study_reminder(pref, user, db)

    except Exception as e:
        logger.error(f"Error executing reminder scheduler: {e}")
    finally:
        db.close()

def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            check_and_send_scheduled_reminders,
            trigger=IntervalTrigger(minutes=1),
            id="daily_study_reminders",
            name="Daily Study Reminders Dispatcher",
            replace_existing=True
        )
        scheduler.start()
        logger.info("MBA Study Hub reminder scheduler started.")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("MBA Study Hub reminder scheduler stopped.")
