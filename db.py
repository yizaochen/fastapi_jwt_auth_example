from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import os
from dotenv import load_dotenv

load_dotenv()
sqlite_db_path = os.getenv("SQLITE_DB_PATH", "example.db")


def get_db():
    """Create a new database session. yield version"""
    engine = create_engine(f"sqlite:///{sqlite_db_path}", echo=False)
    Base.metadata.create_all(engine)  # Ensure all tables are created
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # Ensure the session is closed after use
