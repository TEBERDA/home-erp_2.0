from fastapi import APIRouter, Depends, HTTPException, status, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core import auth
from app.models.auth import User, Household
import uuid

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register")
def register(
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    household_name: str = Form(default=""),
    invite_code: str = Form(default=""),
    db: Session = Depends(get_db)
):
    # Check if user exists
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Handle Household
    household_id = None
    if invite_code:
        household = db.query(Household).filter(Household.invite_code == invite_code).first()
        if not household:
            raise HTTPException(status_code=400, detail="Invalid invite code")
        household_id = household.id
    else:
        # Create new household
        new_household = Household(name=household_name or f"{full_name}'s Home")
        db.add(new_household)
        db.commit()
        db.refresh(new_household)
        household_id = new_household.id

    # Create user
    new_user = User(
        email=email,
        hashed_password=auth.get_password_hash(password),
        full_name=full_name,
        household_id=household_id
    )
    db.add(new_user)
    db.commit()
    
    # Redirect to login
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


@router.post("/login")
def login(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not auth.verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    access_token = auth.create_access_token(data={"sub": user.email})
    
    # Set cookie
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response


@router.get("/logout")
def logout(response: Response):
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response
