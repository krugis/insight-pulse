from datetime import datetime, timedelta, UTC # Use UTC for timezone-aware datetimes
from typing import Optional

from passlib.context import CryptContext #
from jose import JWTError, jwt #

from app.core.config import settings #

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") #

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password) #

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password) #

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES) #
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM) #
    return encoded_jwt

# This function will be used as a FastAPI dependency later
def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]) #
        username: str = payload.get("sub")
        if username is None:
            return None # Token does not contain subject (user identifier)
        return username
    except JWTError: #
        return None # Invalid token