from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.models.activity import ActivityLog

def get_recent_activity(db: Session, household_id: int, limit: int = 10):
    """
    Get the most recent activities for a household.
    """
    return list(db.scalars(
        select(ActivityLog)
        .options(joinedload(ActivityLog.user))
        .where(ActivityLog.household_id == household_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
    ).all())
