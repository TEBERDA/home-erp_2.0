from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.crud import crud_equipment
from app.core.storage import save_upload_file
from app.core.auth import get_current_user
from app.models.auth import User
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter(prefix="/api/v1/equipment", tags=["equipment"])

BASE_DIR = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@router.post("/{equipment_id}/maintenance/{task_id}/do")
def do_maintenance(
    request: Request, 
    equipment_id: int, 
    task_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        crud_equipment.execute_maintenance(db, current_user.household_id, task_id)
        if request.headers.get("HX-Request"):
            eq = crud_equipment.get_equipment(db, current_user.household_id, equipment_id)
            return templates.TemplateResponse(
                request=request,
                name="partials/maintenance_list.html",
                context={"equipment": eq}
            )
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{equipment_id}/documents")
def upload_document(
    equipment_id: int, 
    name: str = Form(...), 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    file_path = save_upload_file(file)
    crud_equipment.add_equipment_document(db, current_user.household_id, equipment_id, name, file_path)
    return {"status": "ok"}

@router.post("/{equipment_id}/maintenance")
def add_maintenance(
    equipment_id: int,
    name: str = Form(...),
    period_days: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    crud_equipment.add_maintenance_task(db, current_user.household_id, equipment_id, name, period_days)
    return {"status": "ok"}
