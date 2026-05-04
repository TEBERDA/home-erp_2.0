from datetime import date, datetime, timedelta
from sqlalchemy import Select, case, func, nulls_last, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.product import Product
from app.models.stock_entry import StockEntry
from app.schemas.inventory import (
    InventoryAdjustmentRequest,
    InventoryConsumeRequest,
    InventoryOverviewItem,
    InventoryPurchaseRequest,
)


def purchase_stock(db: Session, household_id: int, payload: InventoryPurchaseRequest, acting_user=None) -> StockEntry:
    from app.crud.crud_finance import get_or_create_store
    from app.core.activity import log_activity
    from app.crud.product import get_product
    from app.crud.unit import get_unit
    
    store_id = payload.store_id
    if not store_id and payload.store_name:
        store = get_or_create_store(db, household_id, payload.store_name)
        store_id = store.id
        
    stock_entry = StockEntry(
        product_id=payload.product_id,
        amount=payload.amount,
        expiry_date=payload.expiry_date,
        added_date=payload.added_date or datetime.utcnow(),
        price=payload.price,
        store_id=store_id,
        currency=payload.currency,
        household_id=household_id
    )
    db.add(stock_entry)
    db.commit()
    db.refresh(stock_entry)
    
    if acting_user:
        product = get_product(db, household_id, payload.product_id)
        unit = get_unit(db, household_id, product.unit_id)
        log_activity(
            db, 
            acting_user, 
            "inventory_purchase", 
            f"Added {payload.amount} {unit.name} of {product.name}"
        )
        
    return stock_entry


def consume_stock_fifo(db: Session, household_id: int, payload: InventoryConsumeRequest, commit: bool = True, acting_user=None) -> float:
    from app.core.activity import log_activity
    from app.crud.product import get_product
    from app.crud.unit import get_unit
    remaining = payload.amount
    entries_query: Select[tuple[StockEntry]] = (
        select(StockEntry)
        .where(
            StockEntry.product_id == payload.product_id, 
            StockEntry.amount > 0,
            StockEntry.household_id == household_id
        )
        .order_by(nulls_last(StockEntry.expiry_date.asc()), StockEntry.added_date.asc(), StockEntry.id.asc())
    )
    entries = list(db.scalars(entries_query).all())

    for entry in entries:
        if remaining <= 0:
            break
        if entry.amount <= remaining:
            remaining -= entry.amount
            entry.amount = 0.0
        else:
            entry.amount -= remaining
            remaining = 0.0

    if remaining > 0:
        if commit:
            db.rollback()
        raise ValueError("Недостаточно остатков для списания.")

    db.query(StockEntry).filter(
        StockEntry.product_id == payload.product_id,
        StockEntry.amount <= 0,
        StockEntry.household_id == household_id
    ).delete(synchronize_session=False)
    
    if commit:
        db.commit()
        
    if acting_user:
        product = get_product(db, household_id, payload.product_id)
        unit = get_unit(db, household_id, product.unit_id)
        log_activity(
            db, 
            acting_user, 
            "inventory_consume", 
            f"Consumed {payload.amount} {unit.name} of {product.name}"
        )
        
    return payload.amount


def adjust_inventory(db: Session, household_id: int, payload: InventoryAdjustmentRequest, acting_user=None) -> float:
    from app.core.activity import log_activity
    from app.crud.product import get_product
    from app.crud.unit import get_unit
    db.query(StockEntry).filter(
        StockEntry.product_id == payload.product_id,
        StockEntry.household_id == household_id
    ).delete(synchronize_session=False)
    
    if payload.amount > 0:
        db.add(
            StockEntry(
                product_id=payload.product_id,
                amount=payload.amount,
                expiry_date=payload.expiry_date,
                added_date=datetime.utcnow(),
                household_id=household_id
            )
        )
    db.commit()
    
    if acting_user:
        product = get_product(db, household_id, payload.product_id)
        unit = get_unit(db, household_id, product.unit_id)
        log_activity(
            db, 
            acting_user, 
            "inventory_audit", 
            f"Adjusted {product.name} stock to {payload.amount} {unit.name} via audit"
        )
        
    return payload.amount


def get_inventory_overview(db: Session, household_id: int) -> list[InventoryOverviewItem]:
    settings = get_settings()
    today = date.today()
    expiring_limit = today + timedelta(days=settings.expiring_soon_days)

    totals_subquery = (
        select(
            StockEntry.product_id.label("product_id"),
            func.coalesce(func.sum(StockEntry.amount), 0.0).label("total_amount"),
            func.max(case((StockEntry.expiry_date < today, 1), else_=0)).label("has_expired"),
            func.max(
                case(
                    (
                        (StockEntry.expiry_date >= today) & (StockEntry.expiry_date <= expiring_limit),
                        1,
                    ),
                    else_=0,
                )
            ).label("has_expiring"),
        )
        .where(StockEntry.household_id == household_id)
        .group_by(StockEntry.product_id)
        .subquery()
    )

    query = (
        select(
            Product.id,
            Product.name,
            Product.unit_id,
            Product.min_stock_amount,
            func.coalesce(totals_subquery.c.total_amount, 0.0).label("total_amount"),
            func.coalesce(totals_subquery.c.has_expired, 0).label("has_expired"),
            func.coalesce(totals_subquery.c.has_expiring, 0).label("has_expiring"),
        )
        .outerjoin(totals_subquery, totals_subquery.c.product_id == Product.id)
        .where(Product.household_id == household_id)
        .order_by(Product.name.asc())
    )

    rows = db.execute(query).all()
    return [
        InventoryOverviewItem(
            product_id=row.id,
            product_name=row.name,
            unit_id=row.unit_id,
            total_amount=float(row.total_amount),
            min_stock_amount=float(row.min_stock_amount),
            is_below_min_stock=float(row.total_amount) < float(row.min_stock_amount),
            has_expired_items=bool(row.has_expired),
            has_expiring_soon_items=bool(row.has_expiring),
        )
        for row in rows
    ]
