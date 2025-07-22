from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm #
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password, get_password_hash #
from app.crud.user import create_user, get_user_by_email #
from app.schemas.user import UserCreate, UserResponse, Token, LoginRequest #
from app.api.v1.deps import get_db_session, get_current_user #
from app.core.config import settings 
from app.models.user import User 

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db_session) #
):
    db_user = get_user_by_email(db, email=user_in.email) #
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    user = create_user(db=db, user=user_in) #
    return user

@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), #
    db: Session = Depends(get_db_session) #
):
    user = get_user_by_email(db, email=form_data.username) # `username` is actually email for OAuth2PasswordRequestForm
    if not user or not verify_password(form_data.password, user.hashed_password): #
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES) #
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires #
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Example protected route to test authentication
@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)): #
    return current_user