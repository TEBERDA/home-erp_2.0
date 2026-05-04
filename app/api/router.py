from fastapi import APIRouter
from app.api.routes import auth, batteries, chores, equipment, health, household, inventory, locations, pages, products, recipes, shopping_list, units

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(pages.router)
api_router.include_router(units.router)
api_router.include_router(locations.router)
api_router.include_router(products.router)
api_router.include_router(inventory.router)
api_router.include_router(shopping_list.router)
api_router.include_router(recipes.router)
api_router.include_router(chores.router)
api_router.include_router(equipment.router)
api_router.include_router(batteries.router)
api_router.include_router(auth.router)
api_router.include_router(household.router)
