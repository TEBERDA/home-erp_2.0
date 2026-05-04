from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.crud import crud_equipment
from app.core.auth import get_current_user
from app.models.auth import User
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter(prefix="/api/v1/batteries", tags=["batteries"])

BASE_DIR = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@router.post("/{battery_id}/charge")
def charge_battery_endpoint(
    request: Request, 
    battery_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        b = crud_equipment.charge_battery(db, current_user.household_id, battery_id)
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(
                request=request,
                name="partials/battery_item.html",
                context={"battery": b}
            )
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
