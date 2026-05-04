from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.product import get_product
from app.crud.shopping_list import (
    add_shopping_item,
    auto_generate_shopping_list,
    delete_shopping_item,
    get_shopping_items,
)
from app.db.session import get_db
from app.core.auth import get_current_user
from app.models.auth import User
from app.models.shopping_list_item import ShoppingListItem
from app.schemas.shopping_list_item import (
    ShoppingListAutoGenerateResult,
    ShoppingListItemCreate,
    ShoppingListItemRead,
)

router = APIRouter(prefix="/api/v1/shopping-list", tags=["shopping-list"])


@router.get("", response_model=list[ShoppingListItemRead])
def list_shopping_items_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[ShoppingListItemRead]:
    return get_shopping_items(db, current_user.household_id)


@router.post("", response_model=ShoppingListItemRead, status_code=status.HTTP_201_CREATED)
def add_shopping_item_endpoint(
    payload: ShoppingListItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ShoppingListItemRead:
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Количество должно быть больше 0.")
    if not get_product(db, current_user.household_id, payload.product_id):
        raise HTTPException(status_code=404, detail="Продукт не найден.")
    return add_shopping_item(db, current_user.household_id, payload, acting_user=current_user)


@router.post("/auto-generate", response_model=ShoppingListAutoGenerateResult)
def auto_generate_shopping_list_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ShoppingListAutoGenerateResult:
    created = auto_generate_shopping_list(db, current_user.household_id)
    return ShoppingListAutoGenerateResult(created_items=created)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shopping_item_endpoint(
    item_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    item = db.execute(
        select(ShoppingListItem)
        .where(ShoppingListItem.id == item_id, ShoppingListItem.household_id == current_user.household_id)
    ).scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Позиция списка покупок не найдена.")
    delete_shopping_item(db, item)
