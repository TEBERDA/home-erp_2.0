from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session
from app.models.stock_entry import StockEntry, Store
from app.models.product import Product


def get_total_inventory_value(db: Session, household_id: int) -> float:
    # Sum(amount * price) for all current stock entries
    return db.scalar(
        select(func.sum(StockEntry.amount * StockEntry.price))
        .where(StockEntry.amount > 0, StockEntry.household_id == household_id)
    ) or 0.0


def get_product_price_history(db: Session, household_id: int, product_id: int) -> list[dict]:
    entries = db.execute(
        select(StockEntry)
        .where(StockEntry.product_id == product_id, StockEntry.household_id == household_id)
        .where(StockEntry.price.isnot(None))
        .order_by(desc(StockEntry.added_date))
    ).scalars().all()
    
    return [
        {"date": e.added_date, "price": e.price, "currency": e.currency} 
        for e in entries
    ]


def get_best_store_for_product(db: Session, household_id: int, product_id: int) -> Store | None:
    # Find the store where this product had the lowest price
    best_entry = db.execute(
        select(StockEntry)
        .where(StockEntry.product_id == product_id, StockEntry.household_id == household_id)
        .where(StockEntry.price.isnot(None))
        .where(StockEntry.store_id.isnot(None))
        .order_by(StockEntry.price.asc())
        .limit(1)
    ).scalar_one_or_none()
    
    if best_entry:
        return db.execute(
            select(Store).where(Store.id == best_entry.store_id, Store.household_id == household_id)
        ).scalar_one_or_none()
    return None


def get_stores(db: Session, household_id: int) -> list[Store]:
    return list(db.scalars(
        select(Store)
        .where(Store.household_id == household_id)
        .order_by(Store.name)
    ).all())


def get_or_create_store(db: Session, household_id: int, name: str) -> Store:
    store = db.execute(
        select(Store)
        .where(Store.name == name, Store.household_id == household_id)
    ).scalar_one_or_none()
    
    if not store:
        store = Store(name=name, household_id=household_id)
        db.add(store)
        db.commit()
        db.refresh(store)
    return store
