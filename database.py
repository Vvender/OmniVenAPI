from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# .env dosyasını yükle
load_dotenv()

# Ortam değişkeninden DATABASE_URL'i al
DATABASE_URL = os.getenv("DATABASE_URL")

# Hata kontrolü: Değer gelmemişse program baştan hata versin
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in .env file.")

# SQLAlchemy motorunu oluştur
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
