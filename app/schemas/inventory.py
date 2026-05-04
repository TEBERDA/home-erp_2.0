from datetime import date, datetime

from pydantic import BaseModel


class InventoryPurchaseRequest(BaseModel):
    product_id: int
    amount: float
    expiry_date: date | None = None
    added_date: datetime | None = None
    price: float | None = None
    store_id: int | None = None
    store_name: str | None = None
    currency: str = "RUB"


class InventoryConsumeRequest(BaseModel):
    product_id: int
    amount: float


class InventoryAdjustmentRequest(BaseModel):
    product_id: int
    amount: float
    expiry_date: date | None = None


class InventoryOverviewItem(BaseModel):
    product_id: int
    product_name: str
    unit_id: int
    total_amount: float
    min_stock_amount: float
    is_below_min_stock: bool
    has_expired_items: bool
    has_expiring_soon_items: bool
