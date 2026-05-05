from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Chore(Base):
    __tablename__ = "chores"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    period_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    product_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    product_unit_id: Mapped[int | None] = mapped_column(ForeignKey("units.id"), nullable=True)

    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), nullable=False, index=True)

    product = relationship("Product")
    product_unit = relationship("Unit")
    logs = relationship("ChoreLog", back_populates="chore", cascade="all, delete-orphan")


class ChoreLog(Base):
    __tablename__ = "chore_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    chore_id: Mapped[int] = mapped_column(ForeignKey("chores.id"), nullable=False)
    performed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), nullable=False, index=True)

    chore = relationship("Chore", back_populates="logs")
