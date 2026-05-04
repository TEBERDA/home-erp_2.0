from app.db.session import SessionLocal
from app.models.auth import Household, User
from app.models.product import Product

db = SessionLocal()
try:
    h = db.query(Household).first()
    print(f"Household count: {db.query(Household).count()}")
    if h:
        print(f"First Household: {h.name}, Code: {h.invite_code}")
    
    p = db.query(Product).first()
    if p:
        print(f"First Product: {p.name}, Household ID: {p.household_id}")
    
    u = db.query(User).first()
    if u:
        print(f"First User: {u.email}, Household ID: {u.household_id}")
    else:
        print("No users found.")
finally:
    db.close()
