from sqlmodel import SQLModel, create_engine, Session, select
from dotenv import load_dotenv
import os
from datetime import datetime

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
_default_records_created = False

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

def create_default_records_if_empty():
    global _default_records_created, engine
    
    if not _tables_created or engine is None:
        return
    
    if _default_records_created:
        return
    
    try:
        with Session(engine) as session:
            from models import RegistrationFeeDefinition, StampFeeTierDefinition
            
            # Check if registration fees exist
            existing_fees = session.exec(select(RegistrationFeeDefinition)).first()
            if existing_fees is None:
                # Create default registration fees
                default_fees = [
                    RegistrationFeeDefinition(
                        id="government_fee",
                        name="Government Fee",
                        value=0.01,
                        description="Government registration fee",
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    ),
                    RegistrationFeeDefinition(
                        id="ivsl_fee",
                        name="IVSL Fee",
                        value=0.005,
                        description="Internal Valuation Service fee",
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    ),
                    RegistrationFeeDefinition(
                        id="survey_fee",
                        name="Survey Fee",
                        value=0.005,
                        description="Survey plan verification fee",
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    ),
                    RegistrationFeeDefinition(
                        id="notary_fee",
                        name="Notary Fee",
                        value=0.005,
                        description="Notary verification fee",
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    ),
                ]
                for fee in default_fees:
                    session.add(fee)
                session.commit()
            
            # Check if stamp fee tiers exist
            existing_tiers = session.exec(select(StampFeeTierDefinition)).first()
            if existing_tiers is None:
                # Create default stamp fee tiers
                default_tiers = []
                
                # Default tiers for all transaction types
                transaction_types = ["Sale", "Gift", "Transfer", "Exchange", "Lease", "Mortgage"]
                tier_ranges = [
                    (0, 1, 2),
                    (1, 2, 3),
                    (2, 5, 4),
                    (5, 10, 5),
                    (10, None, 6),
                ]
                
                for tx_type in transaction_types:
                    for min_amount, max_amount, percentage in tier_ranges:
                        tier = StampFeeTierDefinition(
                            transaction_type=tx_type,
                            min_amount=min_amount,
                            max_amount=max_amount,
                            percentage=percentage,
                            is_active=True,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        default_tiers.append(tier)
                
                # Also create default tiers (for fallback)
                for min_amount, max_amount, percentage in tier_ranges:
                    tier = StampFeeTierDefinition(
                        transaction_type="Default",
                        min_amount=min_amount,
                        max_amount=max_amount,
                        percentage=percentage,
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    default_tiers.append(tier)
                
                for tier in default_tiers:
                    session.add(tier)
                session.commit()
        
        _default_records_created = True
    except Exception as e:
        print(f"Warning: Could not create default records: {e}")
        _default_records_created = True
