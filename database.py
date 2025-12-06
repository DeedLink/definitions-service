from sqlmodel import SQLModel, create_engine, Session, select
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
_default_record_created = False

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

def create_default_record_if_empty():
    global _default_record_created, engine
    
    if not _tables_created or engine is None:
        return
    
    if _default_record_created:
        return
    
    try:
        with Session(engine) as session:
            from models import PaymentRule
            existing = session.exec(select(PaymentRule)).first()
            if existing is None:
                default_rule = PaymentRule(
                    id="default",
                    type="percentage",
                    value=10.0
                )
                session.add(default_rule)
                session.commit()
        _default_record_created = True
    except Exception as e:
        print(f"Warning: Could not create default record: {e}")
        _default_record_created = True
