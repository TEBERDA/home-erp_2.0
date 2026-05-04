from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ShoppingListItemCreate(BaseModel):
    product_id: int
    amount: float


class ShoppingListItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    amount: float
    added_date: datetime


class ShoppingListAutoGenerateResult(BaseModel):
    created_items: int
