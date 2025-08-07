# routers/dependencies/connection.py
from typing import Annotated, Generator
from sqlalchemy.orm import Session
from fastapi import Depends
from database import SessionLocal  # Absolute import from root

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]