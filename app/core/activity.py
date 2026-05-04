from sqlalchemy.orm import Session
from app.models.activity import ActivityLog
from app.models.auth import User

def log_activity(db: Session, user: User, action_type: str, description: str):
    """
    Log an activity for the household.
    """
    log_entry = ActivityLog(
        household_id=user.household_id,
        user_id=user.id,
        action_type=action_type,
        description=description
    )
    db.add(log_entry)
    db.commit()
