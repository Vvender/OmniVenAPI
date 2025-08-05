from fastapi import HTTPException
from starlette import status
from sqlalchemy.orm import Session
from models import MobileUser


# noinspection PyTypeChecker
def validate_user_unique_fields(
    db: Session,
    email: str | None = None,
    username: str | None = None,
    phone_number: str | None = None,
    exclude_user_id: int | None = None
) -> None:
    conflicts = []

    if email is not None:
        query = db.query(MobileUser).filter(MobileUser.email == email)
        if exclude_user_id:
            query = query.filter(MobileUser.user_id != exclude_user_id)
        if query.first():
            conflicts.append(f"email {email} already in use")

    if username is not None:
        query = db.query(MobileUser).filter(MobileUser.username == username)
        if exclude_user_id:
            query = query.filter(MobileUser.user_id != exclude_user_id)
        if query.first():
            conflicts.append(f"username {username} already in use")

    if phone_number is not None:
        query = db.query(MobileUser).filter(MobileUser.phone_number == phone_number)
        if exclude_user_id:
            query = query.filter(MobileUser.user_id != exclude_user_id)
        if query.first():
            conflicts.append(f"phone number {phone_number} already in use")

    if conflicts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Validation failed",
                "conflicts": conflicts,
                "code": "unique_violation"
            }
        )