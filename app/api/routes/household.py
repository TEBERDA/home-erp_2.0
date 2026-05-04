from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.db.session import get_db
from app.core.auth import get_current_user
from app.models.auth import User, Household

router = APIRouter(prefix="/api/v1/households", tags=["households"])

@router.post("/update")
def update_household(
    name: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    household = current_user.household
    household.name = name
    db.commit()
    return {"status": "ok", "name": name}

@router.post("/regenerate-code")
def regenerate_invite_code(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    household = current_user.household
    household.invite_code = str(uuid.uuid4())[:8].upper()
    db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/settings/household", status_code=status.HTTP_303_SEE_OTHER)
