# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get DATABASE_URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# Validate configuration - fail fast if missing
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not found in .env file")

# Database engine configuration
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Optional: checks connection health before use
    pool_recycle=3600    # Optional: recycle connections after 1 hour
)

# Session factory configuration
SessionLocal = sessionmaker(
    autocommit=False,    # Explicit transaction control
    autoflush=False,     # Manual flush control
    bind=engine          # Bind to our database engine
)

# Dependency for FastAPI routes
def get_db():
    """
    Generator function that yields database sessions.
    Ensures proper session cleanup after request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()