from app.crud.inventory import (
    adjust_inventory,
    consume_stock_fifo,
    get_inventory_overview,
    purchase_stock,
)
from app.crud.location import (
    create_location,
    delete_location,
    get_location,
    get_locations,
    update_location,
)
from app.crud.product import (
    create_product,
    delete_product,
    get_product,
    get_products,
    update_product,
)
from app.crud.shopping_list import (
    add_shopping_item,
    auto_generate_shopping_list,
    delete_shopping_item,
    get_shopping_items,
)
from app.crud.unit import create_unit, delete_unit, get_unit, get_units, update_unit

__all__ = [
    "create_unit",
    "get_units",
    "get_unit",
    "update_unit",
    "delete_unit",
    "create_location",
    "get_locations",
    "get_location",
    "update_location",
    "delete_location",
    "create_product",
    "get_products",
    "get_product",
    "update_product",
    "delete_product",
    "purchase_stock",
    "consume_stock_fifo",
    "adjust_inventory",
    "get_inventory_overview",
    "add_shopping_item",
    "get_shopping_items",
    "delete_shopping_item",
    "auto_generate_shopping_list",
]
