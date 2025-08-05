from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Date, SmallInteger, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class MobileUser(Base):
    __tablename__ = "mobile_users"

    user_id = Column('user_id', Integer, primary_key=True)
    company_id = Column('company_id', Integer, nullable=False, default=0)
    email = Column('email', String(100), nullable=False, unique=True)
    password = Column('password', String(255), nullable=False)
    username = Column('username', String(255), nullable=False, unique=True)
    date_c = Column('date_c', DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    date_expiration = Column('date_expiration', Date, nullable=True)
    date_login = Column(DateTime, onupdate=func.now())
    notification = Column('notification', SmallInteger, nullable=False, default=0)
    verification_code = Column('verification_code', String(6))
    device = Column('device', String(255), nullable=True)
    phone_number = Column('phone_number', String(20), nullable=False, unique=True)
    status = Column('status', SmallInteger, nullable=False, default=1)

    def __repr__(self):
        return f"<MobileUser(user_id={self.user_id}, email='{self.email}')>"