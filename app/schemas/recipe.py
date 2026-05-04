from pydantic import BaseModel, ConfigDict


class RecipeIngredientBase(BaseModel):
    product_id: int
    unit_id: int | None = None
    amount: float


class RecipeIngredientCreate(RecipeIngredientBase):
    pass


class RecipeIngredientUpdate(BaseModel):
    product_id: int | None = None
    unit_id: int | None = None
    amount: float | None = None


class RecipeIngredientRead(RecipeIngredientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recipe_id: int


class RecipeBase(BaseModel):
    name: str
    description: str | None = None
    instructions: str | None = None
    portions: int = 1


class RecipeCreate(RecipeBase):
    ingredients: list[RecipeIngredientCreate] = []


class RecipeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    instructions: str | None = None
    portions: int | None = None
    ingredients: list[RecipeIngredientCreate] | None = None


class RecipeRead(RecipeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ingredients: list[RecipeIngredientRead] = []


class IngredientFulfillmentStatus(BaseModel):
    product_id: int
    product_name: str
    amount_required: float
    current_stock: float
    missing_amount: float
    has_enough: bool


class RecipeFulfillmentResponse(BaseModel):
    can_cook: bool
    ingredients_status: list[IngredientFulfillmentStatus]
