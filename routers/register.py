# register.py
from fastapi import APIRouter, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import text
from datetime import datetime
from routers.dependencies.connection import db_dependency
from routers.schemas.users import MobileUserCreateRequest, MobileUserResponse
from utils.validations import validate_user_unique_fields
from models import MobileUser

# Initialize APIRouter with auth-specific prefix and tags
router = APIRouter(
    prefix="/user/register",  # Base path for all endpoints in this router
    tags=["User"]  # Group in Swagger/OpenAPI docs
)

# Password hashing context using bcrypt algorithm
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


# ------------------------------ REGISTRATION ENDPOINT ------------------------------

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,  # Returns 201 on success
    response_model=MobileUserResponse,  # Shapes the response format
    summary="Register New User",  # Short description in docs
    response_description="The created user object"  # Response explanation
)
async def register_user(
        db: db_dependency,
        user_data: MobileUserCreateRequest
):
    """
    Public user registration endpoint

    Required fields:
    - email: must be unique and valid email format
    - username: 3-255 characters, must be unique
    - password: at least 6 characters
    - phone_number: valid phone number format

    Optional field:
    - company_id: reference to the existing company
    """
    try:
        # Validate company if provided
        if user_data.company_id:
            # Check the company exists in a database
            company_exists = db.execute(
                text("SELECT EXISTS(SELECT 1 FROM acc_company WHERE company_id = :company_id)"),
                {"company_id": user_data.company_id}
            ).scalar()  # Returns True/False

            if not company_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid company ID"
                )

        # Validate unique constraints (email, username, phone)
        validate_user_unique_fields(
            db,
            email=user_data.email,
            username=user_data.username,
            phone_number=user_data.phone_number
        )

        # Create the new user with default values
        new_user = MobileUser(
            company_id=user_data.company_id,  # Maybe None
            email=user_data.email,
            username=user_data.username,
            password=bcrypt_context.hash(user_data.password),  # Hashed password
            status=1,  # Default regular user status
            phone_number=user_data.phone_number,
            date_c=datetime.now(),  # Set a creation timestamp
            date_expiration=None,  # No expiration by default
            notification=True,  # Enable notifications
            device=None  # No device info initially
        )

        # Database operations
        db.add(new_user)
        db.commit()  # Save to a database
        db.refresh(new_user)  # Get updated record with generated IDs
        return new_user

    # Re raise any HTTPExceptions (like validation errors)
    except HTTPException:
        raise

    # Handle any other unexpected errors
    except Exception as e:
        db.rollback()  # Revert uncommitted changes
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User registration failed"
        )