from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    barcode: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    min_stock_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    default_location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), nullable=False)
    
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), nullable=False, index=True)

    default_location = relationship("Location", back_populates="default_products")
    unit = relationship("Unit", back_populates="products")
    stock_entries = relationship("StockEntry", back_populates="product", cascade="all, delete-orphan")
    shopping_list_items = relationship(
        "ShoppingListItem",
        back_populates="product",
        cascade="all, delete-orphan",
    )
