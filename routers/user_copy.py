from fastapi import APIRouter, Path, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import text
from routers.dependencies.connection import db_dependency
from routers.schemas.users import MobileUserRequest, MobileUserResponse
from utils.validations import validate_user_unique_fields
from models import MobileUser

router = APIRouter(
    prefix="/user",
    tags=["User"]
)
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

#*****************************************GET REQUEST*****************************************
@router.get("/", response_model=list[MobileUserResponse], summary="Get all users")
async def get_all_users(db: db_dependency):
    return db.query(MobileUser).all()


@router.get("/{user_id}", response_model=MobileUserResponse, summary="Get user by ID")
async def get_user_by_id(db: db_dependency, user_id: int = Path(..., gt=0)):
    user = db.query(MobileUser).filter(MobileUser.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

#*****************************************POST REQUEST*****************************************
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=MobileUserResponse)
async def create_user(db: db_dependency, user_data: MobileUserRequest):
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

        hashed_password = bcrypt_context.hash(user_data.password)
        new_user = MobileUser(
            company_id=user_data.company_id,
            email=user_data.email,
            username=user_data.username,
            password=hashed_password,
            status=user_data.status,
            phone_number=user_data.phone_number
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    except HTTPException as http_exc:
        # validate_user_unique_fields'dan gelen HTTPException'ı yeniden fırlat
        raise http_exc
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
#*****************************************PUT REQUEST*****************************************
@router.put("/{user_id}", response_model=MobileUserResponse)
async def update_user(
        db: db_dependency,
        user_data: MobileUserRequest,
        user_id: int = Path(gt=0)
):
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

    validate_user_unique_fields(
        db,
        email=user_data.email,
        username=user_data.username,
        phone_number=user_data.phone_number,
        exclude_user_id=user_id
    )

    user.company_id = user_data.company_id
    user.email = user_data.email
    user.username = user_data.username
    user.password = bcrypt_context.hash(user_data.password)
    user.status = user_data.status
    user.phone_number = user_data.phone_number

    db.commit()
    db.refresh(user)
    return user

#*****************************************DELETE REQUEST*****************************************
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(db: db_dependency, user_id: int = Path(gt=0)):
    user = db.query(MobileUser).filter(MobileUser.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    db.delete(user)
    db.commit()