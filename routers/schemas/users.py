from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date

class MobileUserResponse(BaseModel):
    user_id: int
    company_id: int
    email: str
    username: str
    status: int
    phone_number: Optional[str] = None
    date_c: datetime
    date_expiration: Optional[date] = None
    date_login: Optional[datetime] = None
    notification: int
    device: Optional[str] = None

    class Config:
        from_attributes = True

class MobileUserRequest(BaseModel):
    company_id: int = Field(..., gt=0, example=1)
    email: str = Field(..., min_length=3, max_length=100, example="john.smith@example.com")
    username: str = Field(..., min_length=3, max_length=255, example="johnny")
    password: str = Field(..., min_length=6, max_length=50, example="mypassword")
    status: int = Field(default=1, ge=0, le=5)
    phone_number: Optional[str] = Field(
        default=None,
        min_length=5,
        max_length=20,
        pattern=r'^[\d\s\+\-\(\)]{5,20}$',
        example="5004003020"
    )
    date_expiration: Optional[date] = None
    notification: int = Field(default=0)
    device: Optional[str] = Field(default=None, max_length=255)