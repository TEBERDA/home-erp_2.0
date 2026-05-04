from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.location import Location
from app.schemas.location import LocationCreate, LocationUpdate


def create_location(db: Session, household_id: int, payload: LocationCreate) -> Location:
    location = Location(**payload.model_dump(), household_id=household_id)
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


def get_locations(db: Session, household_id: int) -> list[Location]:
    return list(db.scalars(
        select(Location)
        .where(Location.household_id == household_id)
        .order_by(Location.name)
    ).all())


def get_location(db: Session, household_id: int, location_id: int) -> Location | None:
    return db.execute(
        select(Location)
        .where(Location.id == location_id, Location.household_id == household_id)
    ).scalar_one_or_none()


def update_location(db: Session, location: Location, payload: LocationUpdate) -> Location:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(location, field, value)
    db.commit()
    db.refresh(location)
    return location


def delete_location(db: Session, location: Location) -> None:
    db.delete(location)
    db.commit()
