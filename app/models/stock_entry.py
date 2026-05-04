from datetime import date, datetime
from sqlalchemy import Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), nullable=False, index=True)


class StockEntry(Base):
    __tablename__ = "stock_entries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    added_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    
    # Financial fields
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    store_id: Mapped[int | None] = mapped_column(ForeignKey("stores.id"), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="RUB")

    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), nullable=False, index=True)

    product = relationship("Product", back_populates="stock_entries")
    store = relationship("Store")
