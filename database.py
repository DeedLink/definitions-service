from sqlmodel import SQLModel, create_engine
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set. Please set it in your .env file or environment.")

# Use connection pooling for serverless environments
# pool_pre_ping ensures connections are valid before use
engine = create_engine(
    DATABASE_URL, 
    echo=False,  # Disable echo in production
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,
    max_overflow=10
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
