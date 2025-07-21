from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer #
from sqlalchemy.orm import Session

from app.core.database import get_db #
from app.core.security import verify_token #
from app.crud.user import get_user_by_email #
from app.models.user import User #

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/token") #

def get_db_session() -> Generator[Session, None, None]:
    # This function provides a database session to FastAPI dependencies
    # It calls the get_db() generator from app.core.database
    yield from get_db() #

async def get_current_user(
    db: Session = Depends(get_db_session), #
    token: str = Depends(oauth2_scheme) #
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    email = verify_token(token) #
    if email is None:
        raise credentials_exception
    user = get_user_by_email(db, email=email) #
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user