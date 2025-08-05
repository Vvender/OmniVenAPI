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

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

# JWT Settings
SECRET_KEY = "OmniVenAPISecretKey123!@#"  # Must be taken from environment variables in a real project
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 365  # 1 yıl süre

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")


class Token(BaseModel):
    access_token: str
    token_type: str


# noinspection PyTypeChecker
def authenticate_user(username: str, password: str, db: Session):
    user = db.query(MobileUser).filter(MobileUser.username == username).first()
    if not user or not bcrypt_context.verify(password, user.password):
        return None
    return user


def create_access_token(username: str, user_id: int):
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode = {"sub": username, "id": user_id, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: db_dependency
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı",
        )

    access_token = create_access_token(user.username, user.user_id)
    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)], db: db_dependency):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if not username or not user_id:
            raise HTTPException(status_code=401, detail="Geçersiz token")

        return db.query(MobileUser).filter(MobileUser.user_id == user_id).first()

    except JWTError:
        raise HTTPException(status_code=401, detail="Token doğrulanamadı")