# models.py
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Date, SmallInteger, func
from sqlalchemy.ext.declarative import declarative_base

# Base class for SQLAlchemy models
Base = declarative_base()


class MobileUser(Base):
    """
    SQLAlchemy model representing mobile app users in the database.

    Maps to the 'mobile_users' table with fields for user authentication,
    profile information, and account status.
    """
    __tablename__ = "mobile_users"  # Database table name

    # Primary key and identification
    user_id = Column('user_id', Integer, primary_key=True)  # Auto-incremented ID
    company_id = Column('company_id', Integer, nullable=False, default=0)  # Associated company

    # Authentication fields
    email = Column('email', String(100), nullable=False, unique=True)  # Unique email
    password = Column('password', String(255), nullable=False)  # Hashed password storage
    username = Column('username', String(255), nullable=False, unique=True)  # Unique username

    # Timestamps
    date_c = Column('date_c', DateTime, nullable=False,
                    default=lambda: datetime.now(timezone.utc))  # Creation timestamp (UTC)
    date_expiration = Column('date_expiration', Date, nullable=True)  # Optional account expiration
    date_login = Column(DateTime, onupdate=func.now())  # Auto-updated on login

    # Account settings
    notification = Column('notification', SmallInteger, nullable=False, default=0)  # Notification preferences
    verification_code = Column('verification_code', String(6))  # For email/SMS verification
    device = Column('device', String(255), nullable=True)  # Device identifier

    # Contact information
    phone_number = Column('phone_number', String(20), nullable=False, unique=True)  # Unique phone

    # Account status (1=active, etc.)
    status = Column('status', SmallInteger, nullable=False, default=1)

    def __repr__(self):
        """String representation of the user for debugging"""
        return f"<MobileUser(user_id={self.user_id}, email='{self.email}')>"