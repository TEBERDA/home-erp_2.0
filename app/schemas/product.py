from pydantic import BaseModel, ConfigDict

type Barcode = str | None

class ProductBase(BaseModel):
    name: str
    description: str | None = None
    barcode: Barcode = None
    min_stock_amount: float = 0.0
    default_location_id: int | None = None
    unit_id: int


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    barcode: Barcode = None
    min_stock_amount: float | None = None
    default_location_id: int | None = None
    unit_id: int | None = None


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
