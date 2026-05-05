from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.equipment import Equipment, Battery, MaintenanceTask, EquipmentDocument


# Equipment CRUD
def get_equipments(db: Session, household_id: int) -> list[Equipment]:
    return list(db.scalars(
        select(Equipment)
        .where(Equipment.household_id == household_id)
        .order_by(Equipment.name)
    ).all())


def get_equipment(db: Session, household_id: int, equipment_id: int) -> Equipment | None:
    return db.execute(
        select(Equipment)
        .where(Equipment.id == equipment_id, Equipment.household_id == household_id)
    ).scalar_one_or_none()


def create_equipment(db: Session, household_id: int, name: str, description: str = None, serial_number: str = None, purchase_date=None, warranty_expiry=None, location_id: int = None) -> Equipment:
    eq = Equipment(
        name=name,
        description=description,
        serial_number=serial_number,
        purchase_date=purchase_date,
        warranty_expiry=warranty_expiry,
        location_id=location_id,
        household_id=household_id
    )
    db.add(eq)
    db.commit()
    db.refresh(eq)
    return eq


def add_equipment_document(db: Session, household_id: int, equipment_id: int, name: str, file_path: str) -> EquipmentDocument:
    # Ensure equipment belongs to household
    eq = get_equipment(db, household_id, equipment_id)
    if not eq:
        raise ValueError("Equipment not found")
        
    doc = EquipmentDocument(equipment_id=equipment_id, name=name, file_path=file_path, household_id=household_id)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def add_maintenance_task(db: Session, household_id: int, equipment_id: int, name: str, period_days: int) -> MaintenanceTask:
    # Ensure equipment belongs to household
    eq = get_equipment(db, household_id, equipment_id)
    if not eq:
        raise ValueError("Equipment not found")

    task = MaintenanceTask(equipment_id=equipment_id, name=name, period_days=period_days, household_id=household_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def execute_maintenance(db: Session, household_id: int, task_id: int) -> MaintenanceTask:
    task = db.execute(
        select(MaintenanceTask)
        .where(MaintenanceTask.id == task_id, MaintenanceTask.household_id == household_id)
    ).scalar_one_or_none()
    
    if not task:
        raise ValueError("Task not found")
    task.last_done_date = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return task


# Battery CRUD
def get_batteries(db: Session, household_id: int) -> list[Battery]:
    return list(db.scalars(
        select(Battery)
        .where(Battery.household_id == household_id)
        .order_by(Battery.name)
    ).all())


def create_battery(db: Session, household_id: int, name: str, type: str, description: str = None, location_id: int = None) -> Battery:
    b = Battery(name=name, type=type, description=description, location_id=location_id, household_id=household_id)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


def charge_battery(db: Session, household_id: int, battery_id: int) -> Battery:
    b = db.execute(
        select(Battery)
        .where(Battery.id == battery_id, Battery.household_id == household_id)
    ).scalar_one_or_none()
    
    if not b:
        raise ValueError("Battery not found")
    b.last_charge_date = datetime.now(timezone.utc)
    b.charge_cycles += 1
    db.commit()
    db.refresh(b)
    return b


def get_maintenance_alerts(db: Session, household_id: int) -> list[dict]:
    tasks = db.scalars(
        select(MaintenanceTask)
        .where(MaintenanceTask.household_id == household_id)
    ).all()
    alerts = []
    for t in tasks:
        next_due = (t.last_done_date or datetime.min) + timedelta(days=t.period_days)
        if next_due < (datetime.now(timezone.utc) + timedelta(days=3)):
            alerts.append({
                "task": t,
                "next_due": next_due,
                "is_overdue": next_due < datetime.now(timezone.utc)
            })
    return alerts


def get_battery_alerts(db: Session, household_id: int) -> list[dict]:
    batteries = get_batteries(db, household_id)
    alerts = []
    for b in batteries:
        # If not charged for more than 30 days (default threshold)
        if not b.last_charge_date or (datetime.now(timezone.utc) - b.last_charge_date).days > 30:
            alerts.append(b)
    return alerts
