from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.chore import Chore, ChoreLog
from app.models.product import Product
from app.core.units import convert_quantity
from app.crud.inventory import consume_stock_fifo
from app.schemas.inventory import InventoryConsumeRequest


def get_chores(db: Session, household_id: int) -> list[Chore]:
    return list(db.scalars(
        select(Chore)
        .where(Chore.household_id == household_id)
        .order_by(Chore.name)
    ).all())


def get_chores_with_due_date(db: Session, household_id: int) -> list[dict]:
    chores = get_chores(db, household_id)
    result = []
    
    for chore in chores:
        last_log = db.execute(
            select(ChoreLog)
            .where(ChoreLog.chore_id == chore.id, ChoreLog.household_id == household_id)
            .order_by(ChoreLog.performed_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        
        last_performed = last_log.performed_at if last_log else None
        if last_performed:
            next_due = last_performed + timedelta(days=chore.period_days)
        else:
            next_due = datetime.utcnow() # Due now if never performed
            
        result.append({
            "chore": chore,
            "last_performed": last_performed,
            "next_due": next_due,
            "is_overdue": next_due < datetime.utcnow(),
            "is_due_soon": next_due < (datetime.utcnow() + timedelta(days=1))
        })
        
    return result


def create_chore(db: Session, household_id: int, name: str, period_days: int, description: str = None, product_id: int = None, product_amount: float = None, product_unit_id: int = None) -> Chore:
    chore = Chore(
        name=name,
        period_days=period_days,
        description=description,
        product_id=product_id,
        product_amount=product_amount,
        product_unit_id=product_unit_id,
        household_id=household_id
    )
    db.add(chore)
    db.commit()
    db.refresh(chore)
    return chore


def execute_chore(db: Session, household_id: int, chore_id: int, acting_user=None) -> ChoreLog:
    from app.core.activity import log_activity
    chore = db.execute(
        select(Chore)
        .where(Chore.id == chore_id, Chore.household_id == household_id)
    ).scalar_one_or_none()
    
    if not chore:
        raise ValueError("Chore not found")
        
    try:
        # 1. Create log
        log = ChoreLog(chore_id=chore.id, performed_at=datetime.utcnow(), household_id=household_id)
        db.add(log)
        
        # 2. Inventory Integration
        if chore.product_id and chore.product_amount:
            product = db.execute(
                select(Product)
                .where(Product.id == chore.product_id, Product.household_id == household_id)
            ).scalar_one_or_none()
            
            if product:
                # Normalize amount to product's base unit
                amount_to_consume = chore.product_amount
                if chore.product_unit_id and chore.product_unit_id != product.unit_id:
                    amount_to_consume = convert_quantity(
                        db, 
                        chore.product_amount, 
                        chore.product_unit_id, 
                        product.unit_id, 
                        chore.product_id
                    )
                
                consume_stock_fifo(
                    db, 
                    household_id,
                    InventoryConsumeRequest(
                        product_id=chore.product_id, 
                        amount=amount_to_consume
                    ),
                    commit=False
                )
        
        db.commit()

        if acting_user:
            log_activity(db, acting_user, "chore_done", f"Performed chore: {chore.name}")

        return log
    except Exception as e:
        db.rollback()
        raise e
