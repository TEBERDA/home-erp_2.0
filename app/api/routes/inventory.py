from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.crud.inventory import adjust_inventory, consume_stock_fifo, get_inventory_overview, purchase_stock
from app.crud.product import get_product
from app.db.session import get_db
from app.core.auth import get_current_user
from app.models.auth import User
from app.schemas.inventory import (
    InventoryAdjustmentRequest,
    InventoryConsumeRequest,
    InventoryOverviewItem,
    InventoryPurchaseRequest,
)

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])

BASE_DIR = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/overview", response_model=list[InventoryOverviewItem])
def get_overview_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[InventoryOverviewItem]:
    return get_inventory_overview(db, current_user.household_id)


@router.post("/purchase", status_code=status.HTTP_201_CREATED)
def purchase_stock_endpoint(
    payload: InventoryPurchaseRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict[str, str]:
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Количество для закупки должно быть больше 0.")
    if not get_product(db, current_user.household_id, payload.product_id):
        raise HTTPException(status_code=404, detail="Продукт не найден.")
    purchase_stock(db, current_user.household_id, payload, acting_user=current_user)
    return {"status": "ok"}


@router.post("/consume")
def consume_stock_endpoint(
    payload: InventoryConsumeRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict[str, float]:
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Количество для списания должно быть больше 0.")
    if not get_product(db, current_user.household_id, payload.product_id):
        raise HTTPException(status_code=404, detail="Продукт не найден.")
    try:
        consumed = consume_stock_fifo(db, current_user.household_id, payload, acting_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"consumed_amount": consumed}


@router.post("/audit")
async def audit_inventory_endpoint(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Handle both JSON and Form data (HTMX sends form by default)
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        data = await request.json()
        product_id = data.get("product_id")
        amount = data.get("amount")
    else:
        form_data = await request.form()
        product_id = int(form_data.get("product_id"))
        amount = float(form_data.get("amount"))

    if amount < 0:
        raise HTTPException(status_code=400, detail="Инвентаризация не может устанавливать отрицательный остаток.")
    
    product = get_product(db, current_user.household_id, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден.")
    
    adjust_inventory(db, current_user.household_id, InventoryAdjustmentRequest(product_id=product_id, amount=amount), acting_user=current_user)

    if request.headers.get("HX-Request"):
        # Return partial
        return templates.TemplateResponse(
            request=request,
            name="partials/audit_row.html",
            context={
                "item": {
                    "product_id": product_id,
                    "product_name": product.name,
                    "unit_name": product.unit.name if product.unit else "",
                    "total_amount": amount,
                },
                "success": True
            }
        )
    
    return {"amount": amount}
