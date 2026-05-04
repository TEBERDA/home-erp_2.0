from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ShoppingListItem(Base):
    __tablename__ = "shopping_list_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    added_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), nullable=False, index=True)

    product = relationship("Product", back_populates="shopping_list_items")
