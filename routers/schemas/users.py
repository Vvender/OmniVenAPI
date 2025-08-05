# users.py
from pydantic import BaseModel, Field, EmailStr, constr
from typing import Optional
from datetime import date


# Base model for mobile user containing common fields
class MobileUserBase(BaseModel):
    company_id: int = Field(
        ...,  # Required field
        gt=0,  # Must be greater than 0
        json_schema_extra={"example": 1})

    email: EmailStr = Field(  # Email field with built-in validation
        ...,
        json_schema_extra={"example": "john.smith@example.com"})

    username: str = Field(
        ...,
        min_length=3,  # Minimum length constraint
        max_length=255,
        json_schema_extra={"example": "johnny"})

    status: int = Field(
        default=1,  # Default value
        ge=0, le=5)  # Value between 0-5 inclusive

    phone_number: str = Field(
        ...,
        min_length=5,
        max_length=20,
        pattern=r'^[\d\s\+\-\(\)]{5,20}$',  # Regex pattern for validation
        json_schema_extra={"example": "+905004003020"}
    )

    date_expiration: Optional[date] = Field(  # Optional date field
        default=None,
        json_schema_extra={"example": "2025-12-31"})

    notification: int = Field(
        default=0,
        json_schema_extra={"example": 0})

    device: Optional[str] = Field(  # Optional device info
        default=None,
        max_length=255,
        json_schema_extra={"example": "iPhone13,4"})


# Response model excludes password
class MobileUserResponse(MobileUserBase):
    # Keep this but ensure it doesn't require status from create request
    class Config:
        exclude = {"password"}  # Never return passwords


# Update the request model with optional password field
class MobileUserUpdateRequest(MobileUserBase):
    password: Optional[str] = Field(
        default=None,
        min_length=6,
        max_length=255,
        json_schema_extra={"example": "newpassword"})


# Simplified model for user registration (create operation)
class MobileUserCreateRequest(BaseModel):
    """Registration schema with required company_id"""
    email: EmailStr
    username: str
    password: constr(min_length=6)
    phone_number: str
    company_id: int = Field(..., gt=0)  # Required and must be > 0

    # Remove status field completely
    class Config:
        extra = "forbid"  # Prevent unexpected fields