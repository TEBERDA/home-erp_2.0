from datetime import date, datetime
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    warranty_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), nullable=False, index=True)

    location = relationship("Location")
    documents = relationship("EquipmentDocument", back_populates="equipment", cascade="all, delete-orphan")
    maintenance_tasks = relationship("MaintenanceTask", back_populates="equipment", cascade="all, delete-orphan")


class EquipmentDocument(Base):
    __tablename__ = "equipment_documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), nullable=False, index=True)

    equipment = relationship("Equipment", back_populates="documents")


class MaintenanceTask(Base):
    __tablename__ = "maintenance_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    period_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    last_done_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), nullable=False, index=True)

    equipment = relationship("Equipment", back_populates="maintenance_tasks")


class Battery(Base):
    __tablename__ = "batteries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. AA, AAA, Li-Ion
    last_charge_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    charge_cycles: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), nullable=False, index=True)

    location = relationship("Location")
