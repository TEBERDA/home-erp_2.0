from sqlalchemy import func, select
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.recipe import Recipe, RecipeIngredient
from app.models.product import Product
from app.models.stock_entry import StockEntry
from app.models.shopping_list_item import ShoppingListItem
from app.schemas.recipe import RecipeCreate, RecipeUpdate, RecipeFulfillmentResponse, IngredientFulfillmentStatus
from app.schemas.inventory import InventoryConsumeRequest
from app.crud.inventory import consume_stock_fifo


def get_recipes(db: Session, household_id: int) -> list[Recipe]:
    return list(db.scalars(
        select(Recipe)
        .where(Recipe.household_id == household_id)
        .order_by(Recipe.name.asc())
    ).all())


def get_recipe(db: Session, household_id: int, recipe_id: int) -> Recipe | None:
    return db.execute(
        select(Recipe)
        .where(Recipe.id == recipe_id, Recipe.household_id == household_id)
    ).scalar_one_or_none()


def create_recipe(db: Session, household_id: int, payload: RecipeCreate) -> Recipe:
    recipe = Recipe(
        name=payload.name,
        description=payload.description,
        instructions=payload.instructions,
        portions=payload.portions,
        household_id=household_id
    )
    db.add(recipe)
    db.flush()  # Get recipe.id

    for ing in payload.ingredients:
        recipe_ing = RecipeIngredient(
            recipe_id=recipe.id,
            product_id=ing.product_id,
            unit_id=ing.unit_id,
            amount=ing.amount,
            household_id=household_id
        )
        db.add(recipe_ing)
    
    db.commit()
    db.refresh(recipe)
    return recipe


def update_recipe(db: Session, household_id: int, recipe: Recipe, payload: RecipeUpdate) -> Recipe:
    if payload.name is not None:
        recipe.name = payload.name
    if payload.description is not None:
        recipe.description = payload.description
    if payload.instructions is not None:
        recipe.instructions = payload.instructions
    if payload.portions is not None:
        recipe.portions = payload.portions
    
    if payload.ingredients is not None:
        # Simple approach: delete existing and recreate
        db.query(RecipeIngredient).filter(
            RecipeIngredient.recipe_id == recipe.id,
            RecipeIngredient.household_id == household_id
        ).delete()
        for ing in payload.ingredients:
            recipe_ing = RecipeIngredient(
                recipe_id=recipe.id,
                product_id=ing.product_id,
                unit_id=ing.unit_id,
                amount=ing.amount,
                household_id=household_id
            )
            db.add(recipe_ing)
            
    db.commit()
    db.refresh(recipe)
    return recipe


def delete_recipe(db: Session, household_id: int, recipe: Recipe) -> None:
    db.delete(recipe)
    db.commit()


def get_recipe_fulfillment(db: Session, household_id: int, recipe_id: int) -> RecipeFulfillmentResponse:
    from app.core.units import convert_quantity
    recipe = get_recipe(db, household_id, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    ingredients_status = []
    can_cook = True
    
    for ing in recipe.ingredients:
        # Get current stock in base unit
        current_stock = db.scalar(
            select(func.coalesce(func.sum(StockEntry.amount), 0.0))
            .where(StockEntry.product_id == ing.product_id, StockEntry.household_id == household_id)
        ) or 0.0
        
        # Convert required amount to base unit if necessary
        if ing.unit_id and ing.unit_id != ing.product.unit_id:
            try:
                amount_required = convert_quantity(db, ing.amount, ing.unit_id, ing.product.unit_id, ing.product_id)
            except ValueError:
                # Fallback to amount if no conversion found, but this might be wrong
                amount_required = ing.amount
        else:
            amount_required = ing.amount

        has_enough = current_stock >= amount_required
        missing_amount = max(0.0, amount_required - current_stock)
        
        if not has_enough:
            can_cook = False
            
        ingredients_status.append(
            IngredientFulfillmentStatus(
                product_id=ing.product_id,
                product_name=ing.product.name,
                amount_required=amount_required,
                current_stock=current_stock,
                missing_amount=missing_amount,
                has_enough=has_enough,
            )
        )
        
    return RecipeFulfillmentResponse(
        can_cook=can_cook,
        ingredients_status=ingredients_status,
    )


def add_missing_to_shopping_list(db: Session, household_id: int, recipe_id: int) -> int:
    fulfillment = get_recipe_fulfillment(db, household_id, recipe_id)
    added_count = 0
    for status in fulfillment.ingredients_status:
        if status.missing_amount > 0:
            # Check if already in shopping list
            existing = db.execute(
                select(ShoppingListItem)
                .where(ShoppingListItem.product_id == status.product_id, ShoppingListItem.household_id == household_id)
            ).scalar_one_or_none()
            
            if existing:
                existing.amount += status.missing_amount
            else:
                db.add(ShoppingListItem(product_id=status.product_id, amount=status.missing_amount, household_id=household_id))
                added_count += 1
    
    db.commit()
    return added_count


def cook_recipe(db: Session, household_id: int, recipe_id: int, acting_user=None) -> None:
    from app.core.activity import log_activity
    fulfillment = get_recipe_fulfillment(db, household_id, recipe_id)
    if not fulfillment.can_cook:
        raise HTTPException(status_code=400, detail="Not enough ingredients to cook this recipe")
    
    recipe = get_recipe(db, household_id, recipe_id)
    
    try:
        from app.core.units import convert_quantity
        for ing in recipe.ingredients:
            if ing.unit_id and ing.unit_id != ing.product.unit_id:
                amount_to_consume = convert_quantity(db, ing.amount, ing.unit_id, ing.product.unit_id, ing.product_id)
            else:
                amount_to_consume = ing.amount
                
            consume_stock_fifo(db, household_id, InventoryConsumeRequest(product_id=ing.product_id, amount=amount_to_consume), commit=False)
        
        db.commit()

        if acting_user:
            log_activity(db, acting_user, "recipe_cooked", f"Cooked recipe: {recipe.name}")

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error during cooking: {str(e)}")
