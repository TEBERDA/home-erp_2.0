from datetime import date, datetime
from pydantic import BaseModel, Field

type Amount = float

class InventoryPurchaseRequest(BaseModel):
    product_id: int
    amount: Amount = Field(gt=0)
    expiry_date: date | None = None
    added_date: datetime | None = None
    price: float | None = None
    store_id: int | None = None
    store_name: str | None = None
    currency: str = "RUB"


class InventoryConsumeRequest(BaseModel):
    product_id: int
    amount: Amount = Field(gt=0)


class InventoryAdjustmentRequest(BaseModel):
    product_id: int
    amount: Amount = Field(ge=0)
    expiry_date: date | None = None


class InventoryOverviewItem(BaseModel):
    product_id: int
    product_name: str
    unit_id: int
    total_amount: Amount
    min_stock_amount: float
    is_below_min_stock: bool
    has_expired_items: bool
    has_expiring_soon_items: bool
