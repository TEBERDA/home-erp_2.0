from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    portions: Mapped[int] = mapped_column(nullable=False, default=1)
    
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), nullable=False, index=True)

    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), nullable=False, index=True)

    recipe = relationship("Recipe", back_populates="ingredients")
    product = relationship("Product")
    unit = relationship("Unit")
