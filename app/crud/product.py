from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def create_product(db: Session, household_id: int, payload: ProductCreate) -> Product:
    product = Product(**payload.model_dump(), household_id=household_id)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def get_products(db: Session, household_id: int) -> list[Product]:
    return list(db.scalars(
        select(Product)
        .where(Product.household_id == household_id)
        .order_by(Product.name)
    ).all())


def get_product(db: Session, household_id: int, product_id: int) -> Product | None:
    return db.execute(
        select(Product)
        .where(Product.id == product_id, Product.household_id == household_id)
    ).scalar_one_or_none()


def get_product_by_barcode(db: Session, household_id: int, barcode: str) -> Product | None:
    return db.execute(
        select(Product)
        .where(Product.barcode == barcode, Product.household_id == household_id)
    ).scalar_one_or_none()


def update_product(db: Session, product: Product, payload: ProductUpdate) -> Product:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product: Product) -> None:
    db.delete(product)
    db.commit()
