from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from app.models.unit import UnitConversion


def convert_quantity(
    db: Session, 
    amount: float, 
    from_unit_id: int, 
    to_unit_id: int, 
    product_id: int | None = None
) -> float:
    """
    Converts a quantity from one unit to another.
    Checks for product-specific conversions first, then global ones.
    Supports bi-directional conversion.
    """
    if from_unit_id == to_unit_id:
        return amount

    # 1. Look for direct or reverse conversion
    # Priority: Product-specific -> Global
    
    # Try product-specific first
    if product_id:
        conversion = db.execute(
            select(UnitConversion).where(
                UnitConversion.product_id == product_id,
                or_(
                    (UnitConversion.from_unit_id == from_unit_id) & (UnitConversion.to_unit_id == to_unit_id),
                    (UnitConversion.from_unit_id == to_unit_id) & (UnitConversion.to_unit_id == from_unit_id)
                )
            )
        ).scalar_one_or_none()
        
        if conversion:
            if conversion.from_unit_id == from_unit_id:
                return amount * conversion.factor
            else:
                return amount / conversion.factor

    # 2. Try global conversion
    conversion = db.execute(
        select(UnitConversion).where(
            UnitConversion.product_id == None,
            or_(
                (UnitConversion.from_unit_id == from_unit_id) & (UnitConversion.to_unit_id == to_unit_id),
                (UnitConversion.from_unit_id == to_unit_id) & (UnitConversion.to_unit_id == from_unit_id)
            )
        )
    ).scalar_one_or_none()
    
    if conversion:
        if conversion.from_unit_id == from_unit_id:
            return amount * conversion.factor
        else:
            return amount / conversion.factor

    # 3. No conversion found
    raise ValueError(f"No conversion path found from unit {from_unit_id} to {to_unit_id}")


def get_available_units_for_product(db: Session, product_id: int) -> list[int]:
    """
    Returns a list of unit IDs that can be converted to the product's base unit.
    """
    from app.models.product import Product
    product = db.get(Product, product_id)
    if not product:
        return []
    
    base_unit_id = product.unit_id
    
    # Units that have a conversion (direct or reverse) to base_unit_id
    conversions = db.execute(
        select(UnitConversion).where(
            or_(
                UnitConversion.product_id == product_id,
                UnitConversion.product_id == None
            ),
            or_(
                UnitConversion.from_unit_id == base_unit_id,
                UnitConversion.to_unit_id == base_unit_id
            )
        )
    ).scalars().all()
    
    unit_ids = {base_unit_id}
    for c in conversions:
        unit_ids.add(c.from_unit_id)
        unit_ids.add(c.to_unit_id)
        
    return list(unit_ids)
