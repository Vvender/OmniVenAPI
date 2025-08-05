# authentication.py (suggested more descriptive filename)
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session
from routers.dependencies.connection import db_dependency
from models import MobileUser

# Initialize router with clear authentication prefix
router = APIRouter(
    prefix="/authentication",  # More explicit than "/auth"
    tags=["Authentication"]  # Consistent capitalization
)

# Security configuration (should be moved to config/environment in production)
SECRET_KEY = "OmniVenAPISecretKey123!@#"  # In production, use env variables
ALGORITHM = "HS256"  # HMAC with SHA-256
ACCESS_TOKEN_EXPIRE_DAYS = 365  # 1-year expiration

# Password hashing context using bcrypt
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 token bearer scheme
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="authentication/token")


# ------------------------------ MODELS ------------------------------

class Token(BaseModel):
    """JWT Token response model"""
    access_token: str  # The JWT token string
    token_type: str  # Typically "bearer"


# ------------------------------ CORE FUNCTIONS ------------------------------

# noinspection PyTypeChecker
def authenticate_user(username: str, password: str, db: Session) -> MobileUser | None:
    """
    Authenticates user credentials against the database

    Args:
        username: User's login name
        password: Plaintext password to verify
        db: Database session

    Returns:
        MobileUser object if authenticated, None otherwise
    """
    user = db.query(MobileUser).filter(MobileUser.username == username).first()
    if not user or not bcrypt_context.verify(password, user.password):
        return None
    return user


def create_access_token(username: str, user_id: int) -> str:
    """
    Generates a JWT access token

    Args:
        username: Subject for the token
        user_id: User identifier

    Returns:
        Encoded JWT string
    """
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": username,  # Subject claim
        "id": user_id,  # Custom user ID claim
        "exp": expire  # Expiration time
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ------------------------------ API ENDPOINTS ------------------------------

@router.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: db_dependency
) -> dict:
    """
    OAuth2 compatible token login endpoint

    Returns:
        Dictionary with access_token and token_type
    """
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",  # English error message
        )

    token = create_access_token(user.username, user.user_id)
    return {"access_token": token, "token_type": "bearer"}


# ------------------------------ DEPENDENCIES ------------------------------

async def get_current_user(
        token: Annotated[str, Depends(oauth2_bearer)],
        db: db_dependency
) -> MobileUser:
    """
    Dependency to get current authenticated user from JWT token

    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")

        if not username or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )

        user = db.query(MobileUser).filter(MobileUser.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        return user

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )