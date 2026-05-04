from pathlib import Path
from datetime import date, datetime
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.crud.inventory import consume_stock_fifo, get_inventory_overview, purchase_stock
from app.crud.location import get_locations
from app.crud.product import get_products, get_product
from app.crud.shopping_list import add_shopping_item, auto_generate_shopping_list, get_shopping_items
from app.crud.unit import get_units
from app.crud import recipe as crud_recipe
from app.db.session import get_db
from app.core.auth import get_current_user, get_current_user_optional
from app.models.auth import User
from app.schemas.inventory import InventoryConsumeRequest, InventoryPurchaseRequest
from app.schemas.recipe import RecipeCreate, RecipeIngredientCreate, RecipeUpdate
from app.schemas.shopping_list_item import ShoppingListItemCreate
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["pages"])

BASE_DIR = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/", response_class=HTMLResponse)
def landing_page(request: Request, user: User = Depends(get_current_user_optional)) -> HTMLResponse:
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="landing.html", context={"title": "Home ERP"})


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="auth/login.html", context={"title": "Вход"})


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, invite_code: str = "") -> HTMLResponse:
    return templates.TemplateResponse(
        request=request, 
        name="auth/register.html", 
        context={"title": "Регистрация", "invite_code": invite_code}
    )


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> HTMLResponse:
    from app.crud.crud_chores import get_chores_with_due_date
    from app.crud.crud_finance import get_total_inventory_value
    from app.crud.crud_equipment import get_maintenance_alerts, get_battery_alerts
    from app.crud.activity import get_recent_activity
    
    chores = get_chores_with_due_date(db, current_user.household_id)
    due_chores = [c for c in chores if c["is_due_soon"]]
    total_value = get_total_inventory_value(db, current_user.household_id)
    recent_activity = get_recent_activity(db, current_user.household_id, limit=10)
    
    return templates.TemplateResponse(
        request=request,
        name="pages/dashboard.html",
        context={
            "title": "Панель остатков",
            "active_page": "dashboard",
            "inventory": get_inventory_overview(db, current_user.household_id),
            "due_chores": due_chores,
            "total_value": total_value,
            "maintenance_alerts": get_maintenance_alerts(db, current_user.household_id),
            "battery_alerts": get_battery_alerts(db, current_user.household_id),
            "recent_activity": recent_activity,
            "user": current_user,
        },
    )


@router.get("/purchase", response_class=HTMLResponse)
def purchase_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> HTMLResponse:
    from app.crud.crud_finance import get_stores
    return templates.TemplateResponse(
        request=request,
        name="pages/purchase.html",
        context={
            "title": "Поступление",
            "active_page": "purchase",
            "products": get_products(db, current_user.household_id),
            "inventory": get_inventory_overview(db, current_user.household_id),
            "stores": get_stores(db, current_user.household_id),
            "user": current_user,
        },
    )


@router.get("/consume", response_class=HTMLResponse)
def consume_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="pages/consume.html",
        context={
            "title": "Списание",
            "active_page": "consume",
            "products": get_products(db, current_user.household_id),
            "inventory": get_inventory_overview(db, current_user.household_id),
            "user": current_user,
        },
    )


@router.get("/shopping-list", response_class=HTMLResponse)
def shopping_list_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="pages/shopping_list.html",
        context={
            "title": "Список покупок",
            "active_page": "shopping_list",
            "products": get_products(db, current_user.household_id),
            "items": get_shopping_items(db, current_user.household_id),
            "user": current_user,
        },
    )


@router.get("/products", response_class=HTMLResponse)
def products_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="pages/products.html",
        context={
            "title": "Продукты",
            "active_page": "products",
            "products": get_products(db, current_user.household_id),
            "units": get_units(db, current_user.household_id),
            "locations": get_locations(db, current_user.household_id),
            "user": current_user,
        },
    )


@router.get("/locations", response_class=HTMLResponse)
def locations_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="pages/locations.html",
        context={
            "title": "Локации",
            "active_page": "locations",
            "locations": get_locations(db, current_user.household_id),
            "user": current_user,
        },
    )


@router.get("/units", response_class=HTMLResponse)
def units_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> HTMLResponse:
    from app.crud.unit import get_unit_conversions
    return templates.TemplateResponse(
        request=request,
        name="pages/units.html",
        context={
            "title": "Единицы измерения",
            "active_page": "units",
            "units": get_units(db, current_user.household_id),
            "conversions": get_unit_conversions(db, current_user.household_id),
            "products": get_products(db, current_user.household_id),
            "user": current_user,
        },
    )


@router.post("/ui/units/conversions", response_class=HTMLResponse)
def conversion_create_submit(
    request: Request,
    from_unit_id: int = Form(...),
    to_unit_id: int = Form(...),
    factor: float = Form(...),
    product_id: str = Form(default=""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> HTMLResponse:
    from app.crud.unit import create_unit_conversion
    pid = int(product_id) if product_id and product_id != "None" else None
    create_unit_conversion(db, current_user.household_id, from_unit_id, to_unit_id, factor, pid)
    
    response = HTMLResponse(content="", status_code=200)
    response.headers["HX-Redirect"] = "/units"
    return response


@router.post("/ui/purchase", response_class=HTMLResponse)
def purchase_submit(
    request: Request,
    product_id: int = Form(...),
    unit_id: int = Form(...),
    amount: float = Form(...),
    price: float = Form(default=0.0),
    store_id: str = Form(default=""),
    store_name: str = Form(default=""),
    expiry_date: str = Form(default=""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> HTMLResponse:
    from app.core.units import convert_quantity
    
    product = get_product(db, current_user.household_id, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    # Convert amount to base unit
    base_amount = convert_quantity(db, amount, unit_id, product.unit_id, product_id)
    price_per_base_unit = price / base_amount if base_amount > 0 else 0.0
    sid = int(store_id) if store_id and store_id != "None" else None
    
    purchase_stock(
        db,
        current_user.household_id,
        InventoryPurchaseRequest(
            product_id=product_id,
            amount=base_amount,
            expiry_date=expiry_date or None,
            price=price_per_base_unit,
            store_id=sid,
            store_name=store_name,
        ),
        acting_user=current_user
    )
    return templates.TemplateResponse(
        request=request,
        name="partials/inventory_table.html",
        context={"inventory": get_inventory_overview(db, current_user.household_id)},
    )


@router.post("/ui/consume", response_class=HTMLResponse)
def consume_submit(
    request: Request,
    product_id: int = Form(...),
    unit_id: int = Form(...),
    amount: float = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> HTMLResponse:
    from app.core.units import convert_quantity
    
    product = get_product(db, current_user.household_id, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    base_amount = convert_quantity(db, amount, unit_id, product.unit_id, product_id)

    try:
        consume_stock_fifo(db, current_user.household_id, InventoryConsumeRequest(product_id=product_id, amount=base_amount), acting_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return templates.TemplateResponse(
        request=request,
        name="partials/inventory_table.html",
        context={"inventory": get_inventory_overview(db, current_user.household_id)},
    )


@router.post("/ui/shopping-list/add", response_class=HTMLResponse)
def shopping_list_add_submit(
    request: Request,
    product_id: int = Form(...),
    amount: float = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> HTMLResponse:
    add_shopping_item(db, current_user.household_id, ShoppingListItemCreate(product_id=product_id, amount=amount), acting_user=current_user)
    return templates.TemplateResponse(
        request=request,
        name="partials/shopping_list_table.html",
        context={"items": get_shopping_items(db, current_user.household_id)},
    )


@router.post("/ui/shopping-list/auto-generate", response_class=HTMLResponse)
def shopping_list_auto_generate_submit(
    request: Request, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> HTMLResponse:
    auto_generate_shopping_list(db, current_user.household_id)
    return templates.TemplateResponse(
        request=request,
        name="partials/shopping_list_table.html",
        context={"items": get_shopping_items(db, current_user.household_id)},
    )


@router.get("/recipes", response_class=HTMLResponse)
def recipes_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="pages/recipes.html",
        context={
            "title": "Рецепты",
            "active_page": "recipes",
            "recipes": crud_recipe.get_recipes(db, current_user.household_id),
            "user": current_user,
        },
    )


@router.get("/recipes/{recipe_id}", response_class=HTMLResponse)
def recipe_detail_page(request: Request, recipe_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> HTMLResponse:
    recipe = crud_recipe.get_recipe(db, current_user.household_id, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    fulfillment = crud_recipe.get_recipe_fulfillment(db, current_user.household_id, recipe_id)
    return templates.TemplateResponse(
        request=request,
        name="pages/recipe_detail.html",
        context={
            "title": f"Рецепт: {recipe.name}",
            "active_page": "recipes",
            "recipe": recipe,
            "fulfillment": fulfillment,
            "products": get_products(db, current_user.household_id),
            "user": current_user,
        },
    )


@router.post("/ui/recipes", response_class=HTMLResponse)
def recipe_create_submit(
    request: Request,
    name: str = Form(...),
    description: str = Form(default=""),
    instructions: str = Form(default=""),
    portions: int = Form(default=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> HTMLResponse:
    crud_recipe.create_recipe(
        db,
        current_user.household_id,
        RecipeCreate(
            name=name,
            description=description,
            instructions=instructions,
            portions=portions,
        ),
    )
    response = HTMLResponse(content="", status_code=200)
    response.headers["HX-Redirect"] = "/recipes"
    return response


@router.post("/ui/recipes/{recipe_id}/ingredients", response_class=HTMLResponse)
def recipe_add_ingredient_submit(
    request: Request,
    recipe_id: int,
    product_id: int = Form(...),
    unit_id: int = Form(...),
    amount: float = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> HTMLResponse:
    recipe = crud_recipe.get_recipe(db, current_user.household_id, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    current_ingredients = [
        RecipeIngredientCreate(product_id=i.product_id, unit_id=i.unit_id, amount=i.amount) 
        for i in recipe.ingredients
    ]
    current_ingredients.append(RecipeIngredientCreate(product_id=product_id, unit_id=unit_id, amount=amount))
    
    crud_recipe.update_recipe(db, current_user.household_id, recipe, RecipeUpdate(ingredients=current_ingredients))
    
    response = HTMLResponse(content="", status_code=200)
    response.headers["HX-Redirect"] = f"/recipes/{recipe_id}"
    return response


@router.get("/audit", response_class=HTMLResponse)
def audit_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> HTMLResponse:
    inventory = get_inventory_overview(db, current_user.household_id)
    grouped_inventory = {}
    for item in inventory:
        product = get_product(db, current_user.household_id, item.product_id)
        loc_name = product.default_location.name if product and product.default_location else "Без локации"
        if loc_name not in grouped_inventory:
            grouped_inventory[loc_name] = []
        
        unit_name = product.unit.name if product and product.unit else ""
        item_dict = item.model_dump()
        item_dict["unit_name"] = unit_name
        grouped_inventory[loc_name].append(item_dict)

    return templates.TemplateResponse(
        request=request,
        name="pages/audit.html",
        context={
            "title": "Инвентаризация",
            "active_page": "audit",
            "grouped_inventory": grouped_inventory,
            "user": current_user,
        },
    )

@router.get("/ui/partials/units-for-product", response_class=HTMLResponse)
def get_units_for_product_partial(request: Request, product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> HTMLResponse:
    from app.core.units import get_available_units_for_product
    from app.crud.unit import get_unit
    unit_ids = get_available_units_for_product(db, product_id)
    units = [get_unit(db, current_user.household_id, uid) for uid in unit_ids]
    
    return templates.TemplateResponse(
        request=request,
        name="partials/unit_select.html",
        context={"units": units},
    )

@router.get("/chores", response_class=HTMLResponse)
def chores_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> HTMLResponse:
    from app.crud.crud_chores import get_chores_with_due_date
    
    return templates.TemplateResponse(
        request=request,
        name="pages/chores.html",
        context={
            "title": "Домашние дела",
            "active_page": "chores",
            "chores": get_chores_with_due_date(db, current_user.household_id),
            "products": get_products(db, current_user.household_id),
            "units": get_units(db, current_user.household_id),
            "user": current_user,
        },
    )

@router.post("/ui/chores", response_class=HTMLResponse)
def chore_create_submit(
    request: Request,
    name: str = Form(...),
    period_days: int = Form(...),
    description: str = Form(default=""),
    product_id: str = Form(default=""),
    product_amount: float = Form(default=0.0),
    product_unit_id: str = Form(default=""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> HTMLResponse:
    from app.crud.crud_chores import create_chore
    pid = int(product_id) if product_id and product_id != "None" else None
    uid = int(product_unit_id) if product_unit_id and product_unit_id != "None" else None
    create_chore(db, current_user.household_id, name, period_days, description, pid, product_amount, uid)
    
    response = HTMLResponse(content="", status_code=200)
    response.headers["HX-Redirect"] = "/chores"
    return response

@router.get("/equipment", response_class=HTMLResponse)
def equipment_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> HTMLResponse:
    from app.crud.crud_equipment import get_equipments
    return templates.TemplateResponse(
        request=request,
        name="pages/equipment.html",
        context={
            "title": "Техника",
            "active_page": "equipment",
            "equipments": get_equipments(db, current_user.household_id),
            "locations": get_locations(db, current_user.household_id),
            "now_date": date.today(),
            "user": current_user,
        },
    )

@router.get("/equipment/{equipment_id}", response_class=HTMLResponse)
def equipment_detail_page(request: Request, equipment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> HTMLResponse:
    from app.crud.crud_equipment import get_equipment
    eq = get_equipment(db, current_user.household_id, equipment_id)
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return templates.TemplateResponse(
        request=request,
        name="pages/equipment_detail.html",
        context={
            "title": f"Техника: {eq.name}",
            "active_page": "equipment",
            "equipment": eq,
            "user": current_user,
        },
    )

@router.get("/batteries", response_class=HTMLResponse)
def batteries_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> HTMLResponse:
    from app.crud.crud_equipment import get_batteries
    return templates.TemplateResponse(
        request=request,
        name="pages/batteries.html",
        context={
            "title": "Батарейки и аккумуляторы",
            "active_page": "batteries",
            "batteries": get_batteries(db, current_user.household_id),
            "locations": get_locations(db, current_user.household_id),
            "user": current_user,
        },
    )

@router.post("/ui/equipment", response_class=HTMLResponse)
def equipment_create_submit(
    request: Request,
    name: str = Form(...),
    description: str = Form(default=""),
    serial_number: str = Form(default=""),
    purchase_date: str = Form(default=""),
    warranty_expiry: str = Form(default=""),
    location_id: str = Form(default=""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> HTMLResponse:
    from app.crud.crud_equipment import create_equipment
    loc_id = int(location_id) if location_id and location_id != "None" else None
    pd = datetime.strptime(purchase_date, "%Y-%m-%d").date() if purchase_date else None
    we = datetime.strptime(warranty_expiry, "%Y-%m-%d").date() if warranty_expiry else None
    create_equipment(db, current_user.household_id, name, description, serial_number, pd, we, loc_id)
    
    response = HTMLResponse(content="", status_code=200)
    response.headers["HX-Redirect"] = "/equipment"
    return response

@router.post("/ui/batteries", response_class=HTMLResponse)
def battery_create_submit(
    request: Request,
    name: str = Form(...),
    type: str = Form(...),
    description: str = Form(default=""),
    location_id: str = Form(default=""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> HTMLResponse:
    from app.crud.crud_equipment import create_battery
    loc_id = int(location_id) if location_id and location_id != "None" else None
    create_battery(db, current_user.household_id, name, type, description, loc_id)
    
    response = HTMLResponse(content="", status_code=200)
    response.headers["HX-Redirect"] = "/batteries"
    return response

@router.get("/settings/household", response_class=HTMLResponse)
def household_settings_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="pages/household_settings.html",
        context={
            "title": "Настройки домохозяйства",
            "active_page": "settings",
            "user": current_user,
            "household": current_user.household,
            "members": current_user.household.users,
        },
    )
