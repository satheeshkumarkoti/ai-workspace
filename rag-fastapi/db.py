import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from pgvector.sqlalchemy import Vector

load_dotenv()  # loads from local .env automatically

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. DB URL
DATABASE_URL = os.getenv("DATABASE_URL")
print("DB URL:", DATABASE_URL)

# 2. Engine
engine = create_engine(DATABASE_URL, echo=True)

# 3. SessionLocal
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# 4. get_db
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 5. Base
Base = declarative_base()

# 6. Models
class File(Base):
    __tablename__ = "files"
    id           = Column(Integer, primary_key=True, index=True)
    file_name    = Column(String, nullable=False)
    file_content = Column(Text, nullable=False)

class FileChunk(Base):
    __tablename__ = "file_chunks"
    id              = Column(Integer, primary_key=True, index=True)
    file_id         = Column(Integer, ForeignKey("files.id"), nullable=False)
    chunk_text      = Column(Text, nullable=False)
    chunk_embedding = Column(Vector(1536), nullable=True)

# 7. Init DB
def init_db():
    try:
        with engine.connect() as conn:
            conn.execute(__import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            logger.info("pgvector extension enabled.")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

def test_connection():
    try:
        db = SessionLocal()
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        print("DB connection successful!")
        db.close()
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise

if __name__ == "__main__":
    init_db()
    test_connection()