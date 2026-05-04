from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud.location import (
    create_location,
    delete_location,
    get_location,
    get_locations,
    update_location,
)
from app.db.session import get_db
from app.core.auth import get_current_user
from app.models.auth import User
from app.schemas.location import LocationCreate, LocationRead, LocationUpdate

router = APIRouter(prefix="/api/v1/locations", tags=["locations"])


@router.get("", response_model=list[LocationRead])
def list_locations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[LocationRead]:
    return get_locations(db, current_user.household_id)


@router.post("", response_model=LocationRead, status_code=status.HTTP_201_CREATED)
def create_location_endpoint(
    payload: LocationCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> LocationRead:
    try:
        return create_location(db, current_user.household_id, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Не удалось создать локацию.") from exc


@router.get("/{location_id}", response_model=LocationRead)
def get_location_endpoint(
    location_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> LocationRead:
    location = get_location(db, current_user.household_id, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Локация не найдена.")
    return location


@router.put("/{location_id}", response_model=LocationRead)
def update_location_endpoint(
    location_id: int,
    payload: LocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> LocationRead:
    location = get_location(db, current_user.household_id, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Локация не найдена.")
    try:
        return update_location(db, location, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Не удалось обновить локацию.") from exc


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location_endpoint(
    location_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    location = get_location(db, current_user.household_id, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Локация не найдена.")
    delete_location(db, location)
