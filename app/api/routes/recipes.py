from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.crud import recipe as crud_recipe
from app.db.session import get_db
from app.core.auth import get_current_user
from app.models.auth import User
from app.schemas.recipe import (
    RecipeRead,
    RecipeCreate,
    RecipeUpdate,
    RecipeFulfillmentResponse,
    RecipeIngredientCreate,
)

router = APIRouter(prefix="/api/v1/recipes", tags=["recipes"])


@router.get("/", response_model=list[RecipeRead])
def read_recipes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return crud_recipe.get_recipes(db, current_user.household_id)


@router.post("/", response_model=RecipeRead)
def create_recipe(
    payload: RecipeCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return crud_recipe.create_recipe(db, current_user.household_id, payload)


@router.get("/{recipe_id}", response_model=RecipeRead)
def read_recipe(
    recipe_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    recipe = crud_recipe.get_recipe(db, current_user.household_id, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.get("/{recipe_id}/fulfillment", response_model=RecipeFulfillmentResponse)
def get_recipe_fulfillment(
    recipe_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return crud_recipe.get_recipe_fulfillment(db, current_user.household_id, recipe_id)


@router.post("/{recipe_id}/cook")
def cook_recipe(
    recipe_id: int, 
    response: Response, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    crud_recipe.cook_recipe(db, current_user.household_id, recipe_id, acting_user=current_user)
    # Add HX-Trigger to refresh the UI if needed
    response.headers["HX-Trigger"] = "inventoryChanged"
    return {"status": "success", "message": "Recipe cooked and ingredients consumed"}


@router.post("/{recipe_id}/add-missing-to-list")
def add_missing_to_list(
    recipe_id: int, 
    response: Response, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    added_count = crud_recipe.add_missing_to_shopping_list(db, current_user.household_id, recipe_id)
    response.headers["HX-Trigger"] = "shoppingListChanged"
    return {"status": "success", "message": f"Added {added_count} items to shopping list"}


@router.post("/{recipe_id}/ingredients", response_model=RecipeRead)
def add_ingredient_to_recipe(
    recipe_id: int, 
    payload: RecipeIngredientCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    recipe = crud_recipe.get_recipe(db, current_user.household_id, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Update recipe by adding ingredient
    current_ingredients = [
        RecipeIngredientCreate(product_id=i.product_id, amount=i.amount, unit_id=i.unit_id) 
        for i in recipe.ingredients
    ]
    current_ingredients.append(payload)
    
    update_payload = RecipeUpdate(ingredients=current_ingredients)
    return crud_recipe.update_recipe(db, current_user.household_id, recipe, update_payload)
