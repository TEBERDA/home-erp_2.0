from app.schemas.inventory import (
    InventoryAdjustmentRequest,
    InventoryConsumeRequest,
    InventoryOverviewItem,
    InventoryPurchaseRequest,
)
from app.schemas.location import LocationCreate, LocationRead, LocationUpdate
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.schemas.shopping_list_item import (
    ShoppingListAutoGenerateResult,
    ShoppingListItemCreate,
    ShoppingListItemRead,
)
from app.schemas.unit import UnitCreate, UnitRead, UnitUpdate

__all__ = [
    "UnitCreate",
    "UnitRead",
    "UnitUpdate",
    "LocationCreate",
    "LocationRead",
    "LocationUpdate",
    "ProductCreate",
    "ProductRead",
    "ProductUpdate",
    "InventoryPurchaseRequest",
    "InventoryConsumeRequest",
    "InventoryAdjustmentRequest",
    "InventoryOverviewItem",
    "ShoppingListItemCreate",
    "ShoppingListItemRead",
    "ShoppingListAutoGenerateResult",
]
