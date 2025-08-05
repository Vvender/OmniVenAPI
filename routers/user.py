from fastapi import APIRouter, Path, HTTPException, status, Depends
from passlib.context import CryptContext
from sqlalchemy import text
from routers.dependencies.connection import db_dependency
from routers.schemas.users import MobileUserRequest, MobileUserResponse
from utils.validations import validate_user_unique_fields
from models import MobileUser
from datetime import datetime
from typing import Annotated

# JWT için auth modülünden dependency'leri import ediyoruz
from routers.auth import get_current_user

router = APIRouter(
    prefix="/user",
    tags=["User"]
)

# Şifreleme için bcrypt context
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

# Dependency tip tanımı (JWT korumalı endpoint'lerde kullanılacak)
current_user_dependency = Annotated[MobileUser, Depends(get_current_user)]


# *****************************************GET REQUEST*****************************************
@router.get("/", response_model=list[MobileUserResponse], summary="Get all users")
async def get_all_users(db: db_dependency, current_user: current_user_dependency):
    """
    Tüm kullanıcıları listeler (Sadece admin erişebilir)

    - **current_user**: JWT token ile oturum açmış kullanıcı (otomatik alınır)
    """
    # Basit admin kontrolü (status=5 admin kabul ediyoruz)
    if current_user.status != 5:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can access this endpoint"
        )
    return db.query(MobileUser).all()


@router.get("/{user_id}", response_model=MobileUserResponse, summary="Get user by ID")
async def get_user_by_id(
        db: db_dependency,
        user_id: int = Path(..., gt=0),
        current_user: current_user_dependency = None
):
    """
    ID'ye göre kullanıcı getirir

    - **user_id**: Aranan kullanıcının ID'si (1'den büyük olmalı)
    - Admin olmayanlar sadece kendi bilgilerini görebilir
    """
    user = db.query(MobileUser).filter(MobileUser.user_id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Admin değilse ve başka bir kullanıcıyı sorguluyorsa engelle
    if current_user.status != 5 and current_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile"
        )

    return user


@router.get("/me", response_model=MobileUserResponse, summary="Get current user details")
async def get_my_details(current_user: current_user_dependency):
    """
    Oturum açmış kullanıcının kendi bilgilerini getirir

    - Token gerektirir
    - Kullanıcıyı veritabanından tekrar sorgulamaz, token'dan alır
    """
    return current_user


# *****************************************POST REQUEST*****************************************
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=MobileUserResponse)
async def create_user(
        db: db_dependency,
        user_data: MobileUserRequest,
        current_user: current_user_dependency = None
):
    """
    Yeni kullanıcı oluşturur (Adminler için)

    - Şirket varlığını kontrol eder
    - Benzersiz alanları validate eder
    - Şifreyi hash'ler
    """
    # Eğer admin kontrolü istiyorsanız:
    if current_user and current_user.status != 5:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can create new users"
        )

    try:
        # Şirket kontrolü
        company = db.execute(
            text("SELECT 1 FROM acc_company WHERE company_id = :company_id"),
            {"company_id": user_data.company_id}
        ).first()

        if not company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Company with ID {user_data.company_id} does not exist"
            )

        # Benzersiz alan kontrolü
        validate_user_unique_fields(
            db,
            email=user_data.email,
            username=user_data.username,
            phone_number=user_data.phone_number
        )

        # Şifreyi hash'le
        hashed_password = bcrypt_context.hash(user_data.password)

        # Yeni kullanıcı oluştur
        new_user = MobileUser(
            company_id=user_data.company_id,
            email=user_data.email,
            username=user_data.username,
            password=hashed_password,
            status=user_data.status,
            phone_number=user_data.phone_number,
            date_c=datetime.now(),
            date_expiration=user_data.date_expiration,
            notification=user_data.notification,
            device=user_data.device
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# *****************************************PUT REQUEST*****************************************
@router.put("/{user_id}", response_model=MobileUserResponse)
async def update_user(
        db: db_dependency,
        user_data: MobileUserRequest,
        user_id: int = Path(gt=0),
        current_user: current_user_dependency = None
):
    """
    Kullanıcı bilgilerini günceller

    - Adminler tüm kullanıcıları güncelleyebilir
    - Normal kullanıcılar sadece kendi bilgilerini güncelleyebilir
    """
    # Yetki kontrolü
    if current_user and current_user.status != 5 and current_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )

    # Şirket kontrolü
    company = db.execute(
        text("SELECT 1 FROM acc_company WHERE company_id = :company_id"),
        {"company_id": user_data.company_id}
    ).first()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Company with ID {user_data.company_id} does not exist"
        )

    user = db.query(MobileUser).filter(MobileUser.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Güncelleme için benzersiz alan kontrolü (mevcut kullanıcıyı hariç tut)
    validate_user_unique_fields(
        db,
        email=user_data.email,
        username=user_data.username,
        phone_number=user_data.phone_number,
        exclude_user_id=user_id
    )

    # Alanları güncelle
    user.company_id = user_data.company_id
    user.email = user_data.email
    user.username = user_data.username
    user.status = user_data.status
    user.phone_number = user_data.phone_number
    user.date_expiration = user_data.date_expiration
    user.notification = user_data.notification
    user.device = user_data.device

    # Şifre değişmişse hash'le
    if user_data.password:
        user.password = bcrypt_context.hash(user_data.password)

    db.commit()
    db.refresh(user)
    return user


# *****************************************DELETE REQUEST*****************************************
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
        db: db_dependency,
        user_id: int = Path(gt=0),
        current_user: current_user_dependency = None
):
    """
    Kullanıcı siler

    - Adminler tüm kullanıcıları silebilir
    - Normal kullanıcılar sadece kendilerini silebilir
    """
    # Yetki kontrolü
    if current_user and current_user.status != 5 and current_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own account"
        )

    user = db.query(MobileUser).filter(MobileUser.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    db.delete(user)
    db.commit()