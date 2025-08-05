# validations.py
from fastapi import HTTPException
from pydantic import EmailStr
from starlette import status
from sqlalchemy.orm import Session
from models import MobileUser


# noinspection PyTypeChecker
def validate_user_unique_fields(
        db: Session,  # Database session for queries
        email: EmailStr | None = None,  # Optional email to validate
        username: str | None = None,  # Optional username to validate
        phone_number: str | None = None,  # Optional phone number to validate
        exclude_user_id: int | None = None  # Optional user ID to exclude from checks
) -> None:
    """
    Validates the uniqueness of user fields in the database.
    Raises HTTPException with conflict details if any duplicates are found.

    Args:
        db: Database session
        email: Email to check for uniqueness
        username: Username to check for uniqueness
        phone_number: Phone number to check for uniqueness
        exclude_user_id: When updating, exclude this user from duplicate checks

    Raises:
        HTTPException: 400 Bad Request with conflict details if duplicates exist
    """
    conflicts = {}  # Dictionary to collect validation errors

    # Email uniqueness check
    if email is not None:
        exists = db.query(MobileUser.user_id).filter(MobileUser.email == str(email))
        if exclude_user_id:  # For update operations
            exists = exists.filter(MobileUser.user_id != exclude_user_id)
        if exists.first():  # If record exists
            conflicts["email"] = "Email already in use"

    # Username uniqueness check
    if username is not None:
        query = db.query(MobileUser).filter(MobileUser.username == username)
        if exclude_user_id:  # For update operations
            query = query.filter(MobileUser.user_id != exclude_user_id)
        if query.first():  # If record exists
            conflicts["username"] = "Username already in use"

    # Phone number uniqueness check
    if phone_number is not None:
        query = db.query(MobileUser).filter(MobileUser.phone_number == phone_number)
        if exclude_user_id:  # For update operations
            query = query.filter(MobileUser.user_id != exclude_user_id)
        if query.first():  # If record exists
            conflicts["phone_number"] = "Phone number already in use"

    # If any conflicts found, raise HTTPException
    if conflicts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Validation errors",
                "errors": conflicts  # Detailed conflict information
            }
        )