from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Unit(Base):
    __tablename__ = "units"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    household_id: Mapped[int | None] = mapped_column(ForeignKey("households.id"), nullable=True) # Nullable for global units

    products = relationship("Product", back_populates="unit")


class UnitConversion(Base):
    __tablename__ = "unit_conversions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    from_unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), nullable=False)
    to_unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), nullable=False)
    factor: Mapped[float] = mapped_column(Float, nullable=False)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), nullable=False, index=True)

    from_unit = relationship("Unit", foreign_keys=[from_unit_id])
    to_unit = relationship("Unit", foreign_keys=[to_unit_id])
    product = relationship("Product")
