from datetime import datetime
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.shopping_list_item import ShoppingListItem
from app.models.stock_entry import StockEntry
from app.schemas.shopping_list_item import ShoppingListItemCreate


def add_shopping_item(db: Session, household_id: int, payload: ShoppingListItemCreate, acting_user=None) -> ShoppingListItem:
    from app.core.activity import log_activity
    from app.crud.product import get_product
    item = ShoppingListItem(
        product_id=payload.product_id,
        amount=payload.amount,
        added_date=datetime.utcnow(),
        household_id=household_id
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    
    if acting_user:
        product = get_product(db, household_id, payload.product_id)
        log_activity(db, acting_user, "shopping_list_add", f"Added {product.name} to shopping list")
        
    return item


def get_shopping_items(db: Session, household_id: int) -> list[ShoppingListItem]:
    return list(db.scalars(
        select(ShoppingListItem)
        .where(ShoppingListItem.household_id == household_id)
        .order_by(ShoppingListItem.added_date.desc())
    ).all())


def delete_shopping_item(db: Session, item: ShoppingListItem) -> None:
    db.delete(item)
    db.commit()


def auto_generate_shopping_list(db: Session, household_id: int) -> int:
    totals_subquery = (
        select(
            StockEntry.product_id.label("product_id"),
            func.coalesce(func.sum(StockEntry.amount), 0.0).label("total_amount"),
        )
        .where(StockEntry.household_id == household_id)
        .group_by(StockEntry.product_id)
        .subquery()
    )
    query = (
        select(
            Product.id,
            Product.min_stock_amount,
            func.coalesce(totals_subquery.c.total_amount, 0.0).label("total_amount"),
        )
        .outerjoin(totals_subquery, totals_subquery.c.product_id == Product.id)
        .where(Product.household_id == household_id)
    )

    created = 0
    for row in db.execute(query).all():
        missing_amount = float(row.min_stock_amount) - float(row.total_amount)
        if missing_amount > 0:
            # Check if already in shopping list
            existing = db.execute(
                select(ShoppingListItem)
                .where(ShoppingListItem.product_id == row.id, ShoppingListItem.household_id == household_id)
            ).scalar_one_or_none()
            
            if not existing:
                db.add(
                    ShoppingListItem(
                        product_id=row.id,
                        amount=missing_amount,
                        added_date=datetime.utcnow(),
                        household_id=household_id
                    )
                )
                created += 1

    db.commit()
    return created
