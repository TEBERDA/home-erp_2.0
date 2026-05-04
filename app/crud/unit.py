from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.models.unit import Unit, UnitConversion
from app.schemas.unit import UnitCreate, UnitUpdate


def create_unit(db: Session, household_id: int, payload: UnitCreate) -> Unit:
    unit = Unit(**payload.model_dump(), household_id=household_id)
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


def get_units(db: Session, household_id: int) -> list[Unit]:
    return list(db.scalars(
        select(Unit)
        .where(or_(Unit.household_id == household_id, Unit.household_id.is_(None)))
        .order_by(Unit.name)
    ).all())


def get_unit(db: Session, household_id: int, unit_id: int) -> Unit | None:
    return db.execute(
        select(Unit)
        .where(Unit.id == unit_id)
        .where(or_(Unit.household_id == household_id, Unit.household_id.is_(None)))
    ).scalar_one_or_none()


def update_unit(db: Session, unit: Unit, payload: UnitUpdate) -> Unit:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(unit, field, value)
    db.commit()
    db.refresh(unit)
    return unit


def delete_unit(db: Session, unit: Unit) -> None:
    db.delete(unit)
    db.commit()


def get_unit_conversions(db: Session, household_id: int) -> list[UnitConversion]:
    return list(db.scalars(
        select(UnitConversion)
        .where(UnitConversion.household_id == household_id)
    ).all())


def create_unit_conversion(
    db: Session, 
    household_id: int,
    from_unit_id: int, 
    to_unit_id: int, 
    factor: float, 
    product_id: int | None = None
) -> UnitConversion:
    conversion = UnitConversion(
        from_unit_id=from_unit_id,
        to_unit_id=to_unit_id,
        factor=factor,
        product_id=product_id,
        household_id=household_id
    )
    db.add(conversion)
    db.commit()
    db.refresh(conversion)
    return conversion


def delete_unit_conversion(db: Session, household_id: int, conversion_id: int) -> None:
    conversion = db.execute(
        select(UnitConversion)
        .where(UnitConversion.id == conversion_id, UnitConversion.household_id == household_id)
    ).scalar_one_or_none()
    if conversion:
        db.delete(conversion)
        db.commit()
