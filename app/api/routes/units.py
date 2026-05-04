from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud.unit import create_unit, delete_unit, get_unit, get_units, update_unit
from app.db.session import get_db
from app.core.auth import get_current_user
from app.models.auth import User
from app.schemas.unit import UnitCreate, UnitRead, UnitUpdate

router = APIRouter(prefix="/api/v1/units", tags=["units"])


@router.get("", response_model=list[UnitRead])
def list_units(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[UnitRead]:
    return get_units(db, current_user.household_id)


@router.post("", response_model=UnitRead, status_code=status.HTTP_201_CREATED)
def create_unit_endpoint(
    payload: UnitCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UnitRead:
    try:
        return create_unit(db, current_user.household_id, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Не удалось создать единицу измерения.") from exc


@router.get("/{unit_id}", response_model=UnitRead)
def get_unit_endpoint(
    unit_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UnitRead:
    unit = get_unit(db, current_user.household_id, unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Единица измерения не найдена.")
    return unit


@router.put("/{unit_id}", response_model=UnitRead)
def update_unit_endpoint(
    unit_id: int, 
    payload: UnitUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UnitRead:
    unit = get_unit(db, current_user.household_id, unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Единица измерения не найдена.")
    try:
        return update_unit(db, unit, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Не удалось обновить единицу измерения.") from exc


@router.delete("/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_unit_endpoint(
    unit_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    unit = get_unit(db, current_user.household_id, unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Единица измерения не найдена.")
    # Check if it's a global unit (household_id is NULL)
    if unit.household_id is None:
        raise HTTPException(status_code=403, detail="Нельзя удалять системные единицы измерения.")
    delete_unit(db, unit)


@router.get("/for-product/{product_id}", response_model=list[UnitRead])
def get_units_for_product(
    product_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.core.units import get_available_units_for_product
    # Need to check if product belongs to household
    from app.crud.product import get_product
    if not get_product(db, current_user.household_id, product_id):
        raise HTTPException(status_code=404, detail="Продукт не найден.")
        
    unit_ids = get_available_units_for_product(db, product_id)
    return [get_unit(db, current_user.household_id, uid) for uid in unit_ids]
