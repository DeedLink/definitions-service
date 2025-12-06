from sqlmodel import SQLModel, create_engine
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    engine = create_engine(
        DATABASE_URL, 
        echo=False,
        pool_pre_ping=True,
        pool_size=1,
        max_overflow=0,
        connect_args={"connect_timeout": 10}
    )
else:
    engine = None

_tables_created = False

def create_db_and_tables():
    global _tables_created, engine
    
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set. Please set it in Vercel environment variables.")
    
    if engine is None:
        raise ValueError("Database engine not initialized. DATABASE_URL is required.")
    
    if not _tables_created:
        try:
            SQLModel.metadata.create_all(engine)
            _tables_created = True
        except Exception as e:
            print(f"Warning: Could not create tables: {e}")
            _tables_created = True
