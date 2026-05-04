from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.crud import crud_chores
from app.core.auth import get_current_user
from app.models.auth import User
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter(prefix="/api/v1/chores", tags=["chores"])

BASE_DIR = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@router.post("/{chore_id}/execute")
def execute_chore_endpoint(
    request: Request,
    chore_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        crud_chores.execute_chore(db, current_user.household_id, chore_id, acting_user=current_user)
        
        if request.headers.get("HX-Request"):
            chores_with_due = crud_chores.get_chores_with_due_date(db, current_user.household_id)
            updated_item = next((c for c in chores_with_due if c["chore"].id == chore_id), None)
            
            return templates.TemplateResponse(
                request=request,
                name="partials/chore_item.html",
                context={"item": updated_item}
            )
            
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing chore: {str(e)}")
