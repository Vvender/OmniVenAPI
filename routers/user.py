from fastapi import APIRouter, Path, HTTPException, status, Depends
from passlib.context import CryptContext
from sqlalchemy import text
from datetime import datetime, timezone
from typing import Annotated, List

# Import dependencies and schemas
from routers.dependencies.connection import db_dependency
from routers.schemas.users import (
    MobileUserResponse,
    MobileUserUpdateRequest,
    MobileUserCreateRequest
)
from utils.validations import validate_user_unique_fields
from models import MobileUser
from routers.authentication import get_current_user

# Initialize APIRouter with prefix and tags for Swagger docs
router = APIRouter(
    prefix="/user",
    tags=["User"]
)

# Password hashing context using bcrypt
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

# Dependency to get the current authenticated user
current_user_dependency = Annotated[MobileUser, Depends(get_current_user)]

#------------------------------ HELPER FUNCTIONS ------------------------------

def verify_admin(current_user: MobileUser):
    """Check if a user has admin privileges (status=5)"""
    if current_user.status != 5:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

def verify_owner_or_admin(current_user: MobileUser, user_id: int):
    """Verify if the requester is the account owner or an admin"""
    if current_user.user_id != user_id and current_user.status != 5:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

def check_company_exists(db: db_dependency, company_id: int):
    """Validate that company exists in a database"""
    if not db.execute(
            text("SELECT 1 FROM acc_company WHERE company_id = :company_id"),
            {"company_id": company_id}
    ).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid company ID"
        )

#------------------------------ GET ENDPOINTS ------------------------------

@router.get("/", response_model=List[MobileUserResponse])
async def list_users(
        db: db_dependency,
        current_user: current_user_dependency
):
    """Get all users (Admin-only endpoint)"""
    verify_admin(current_user)
    return db.query(MobileUser).all()

@router.get("/{user_id}", response_model=MobileUserResponse)
async def get_user(
        db: db_dependency,
        user_id: int = Path(..., gt=0),  # Path parameter must be > 0
        current_user: current_user_dependency = None
):
    """Get the specific user by ID (Owner or Admin only)"""
    user = db.query(MobileUser).filter(MobileUser.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    verify_owner_or_admin(current_user, user_id)
    return user

@router.get("/me", response_model=MobileUserResponse)
async def get_current_user(current_user: current_user_dependency):
    """Get profile of currently authenticated user"""
    return current_user

#------------------------------ POST ENDPOINT ------------------------------

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=MobileUserResponse)
async def create_user(
        db: db_dependency,
        user_data: MobileUserCreateRequest,
        current_user: current_user_dependency
):
    verify_admin(current_user)

    # At First validate company exists
    company_exists = db.execute(
        text("SELECT 1 FROM acc_company WHERE company_id = :company_id"),
        {"company_id": user_data.company_id}
    ).scalar()

    if not company_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid company ID"
        )

    new_user = MobileUser(
        company_id=user_data.company_id,  # Now required
        email=user_data.email,
        username=user_data.username,
        password=bcrypt_context.hash(user_data.password),
        phone_number=user_data.phone_number,
        status=1,  # Server-side default
        date_c=datetime.now(timezone.utc),
        notification=0,  # Default
        device=None  # Explicit None for optional fields
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User creation failed"
        )

#------------------------------ PUT ENDPOINT ------------------------------

@router.put("/{user_id}", response_model=MobileUserResponse)
async def update_user(
        db: db_dependency,
        user_data: MobileUserUpdateRequest,
        user_id: int = Path(..., gt=0),
        current_user: current_user_dependency = None
):
    """Update user profile (Owner or Admin only)"""
    user = db.query(MobileUser).filter(MobileUser.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    verify_owner_or_admin(current_user, user_id)
    check_company_exists(db, user_data.company_id)

    # Validate unique fields excluding current user
    validate_user_unique_fields(
        db,
        email=user_data.email,
        username=user_data.username,
        phone_number=user_data.phone_number,
        exclude_user_id=user_id
    )

    # Update all fields
    user.company_id = user_data.company_id
    user.email = user_data.email
    user.username = user_data.username
    user.status = user_data.status
    user.phone_number = user_data.phone_number
    user.date_expiration = user_data.date_expiration
    user.notification = user_data.notification
    user.device = user_data.device

    # Update password only if provided
    if user_data.password:
        user.password = bcrypt_context.hash(user_data.password)

    try:
        db.commit()
        db.refresh(user)
        return user
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )

#------------------------------ DELETE ENDPOINT ------------------------------

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
        db: db_dependency,
        user_id: int = Path(..., gt=0),
        current_user: current_user_dependency = None
):
    """Delete the user account (Owner or Admin only)"""
    user = db.query(MobileUser).filter(MobileUser.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    verify_owner_or_admin(current_user, user_id)

    try:
        db.delete(user)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Account deletion failed"
        )