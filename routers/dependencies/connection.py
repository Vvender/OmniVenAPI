# routers/dependencies/connection.py (updated)
from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends
from database import SessionLocal  # Absolute import from root

def get_db():
    """Database session generator"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]