from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud.location import get_location
import httpx
from app.crud.product import (
    create_product,
    delete_product,
    get_product,
    get_product_by_barcode,
    get_products,
    update_product,
)
from app.crud.unit import get_unit
from app.db.session import get_db
from app.core.auth import get_current_user
from app.models.auth import User
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate

router = APIRouter(prefix="/api/v1/products", tags=["products"])


@router.get("/by-barcode/{barcode}")
async def get_product_by_barcode_endpoint(
    barcode: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Check local database
    product = get_product_by_barcode(db, current_user.household_id, barcode)
    if product:
        return {
            "found_locally": True,
            "found_external": False,
            "product": ProductRead.model_validate(product)
        }

    # 2. Check Open Food Facts API
    url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == 1:
                    product_data = data.get("product", {})
                    return {
                        "found_locally": False,
                        "found_external": True,
                        "name": product_data.get("product_name") or product_data.get("product_name_ru") or "Unknown Product",
                        "image": product_data.get("image_url"),
                        "barcode": barcode
                    }
        except Exception:
            pass

    # 3. Not found anywhere
    return {"found_locally": False, "found_external": False}


@router.get("", response_model=list[ProductRead])
def list_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[ProductRead]:
    return get_products(db, current_user.household_id)


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product_endpoint(
    payload: ProductCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ProductRead:
    if not get_unit(db, current_user.household_id, payload.unit_id):
        raise HTTPException(status_code=400, detail="Указанная единица измерения не существует.")
    if payload.default_location_id and not get_location(db, current_user.household_id, payload.default_location_id):
        raise HTTPException(status_code=400, detail="Указанная локация не существует.")
    try:
        return create_product(db, current_user.household_id, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Не удалось создать продукт.") from exc


@router.get("/{product_id}", response_model=ProductRead)
def get_product_endpoint(
    product_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ProductRead:
    product = get_product(db, current_user.household_id, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден.")
    return product


@router.put("/{product_id}", response_model=ProductRead)
def update_product_endpoint(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ProductRead:
    product = get_product(db, current_user.household_id, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден.")

    if payload.unit_id is not None and not get_unit(db, current_user.household_id, payload.unit_id):
        raise HTTPException(status_code=400, detail="Указанная единица измерения не существует.")
    if payload.default_location_id is not None and not get_location(db, current_user.household_id, payload.default_location_id):
        raise HTTPException(status_code=400, detail="Указанная локация не существует.")

    try:
        return update_product(db, product, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Не удалось обновить продукт.") from exc


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_endpoint(
    product_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    product = get_product(db, current_user.household_id, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден.")
    delete_product(db, product)
