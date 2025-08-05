from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends
from database import SessionLocal

def get_db():
    """Generator function that provides a database session for each request.
    Ensures the session is properly closed after request completion."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency type annotation for FastAPI route parameters
# Injects a fresh database session for each request
db_dependency = Annotated[Session, Depends(get_db)]