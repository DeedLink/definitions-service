from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import Optional, List
from models import (
    RegistrationFeeDefinition, RegistrationFeeDefinitionCreate, RegistrationFeeDefinitionUpdate,
    StampFeeTierDefinition, StampFeeTierDefinitionCreate, StampFeeTierDefinitionUpdate,
    RegistrationFeesResponse, StampFeeTier, StampFeeTiersResponse, AllStampFeeTiersResponse,
    CalculateStampFeeRequest, CalculateStampFeeResponse
)
from database import engine, create_db_and_tables, create_default_records_if_empty
from datetime import datetime

app = FastAPI(
    title="DeedLink Definitions Service",
    description="API for managing registration fees and stamp fee tier definitions",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_session():
    create_db_and_tables()
    create_default_records_if_empty()
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()

# ==================== Registration Fees Endpoints ====================

@app.get("/registration-fees", response_model=RegistrationFeesResponse)
def get_registration_fees(session: Session = Depends(get_session)):
    """Get all active registration fees"""
    fees = session.exec(
        select(RegistrationFeeDefinition).where(RegistrationFeeDefinition.is_active == True)
    ).all()
    
    fee_dict = {fee.id: fee.value for fee in fees}
    
    return RegistrationFeesResponse(
        government_fee=fee_dict.get("government_fee", 0.01),
        ivsl_fee=fee_dict.get("ivsl_fee", 0.005),
        survey_fee=fee_dict.get("survey_fee", 0.005),
        notary_fee=fee_dict.get("notary_fee", 0.005),
        total_registration_fee=sum([
            fee_dict.get("government_fee", 0.01),
            fee_dict.get("ivsl_fee", 0.005),
            fee_dict.get("survey_fee", 0.005),
            fee_dict.get("notary_fee", 0.005),
        ])
    )

@app.get("/registration-fees/all", response_model=List[RegistrationFeeDefinition])
def get_all_registration_fees(session: Session = Depends(get_session)):
    """Get all registration fee definitions (including inactive)"""
    fees = session.exec(select(RegistrationFeeDefinition)).all()
    return list(fees)

@app.get("/registration-fees/{fee_id}", response_model=RegistrationFeeDefinition)
def get_registration_fee(fee_id: str, session: Session = Depends(get_session)):
    """Get a specific registration fee by ID"""
    fee = session.get(RegistrationFeeDefinition, fee_id)
    if not fee:
        raise HTTPException(status_code=404, detail="Registration fee not found")
    return fee

@app.post("/registration-fees", response_model=RegistrationFeeDefinition)
def create_registration_fee(fee: RegistrationFeeDefinitionCreate, session: Session = Depends(get_session)):
    """Create a new registration fee definition"""
    existing = session.get(RegistrationFeeDefinition, fee.id)
    if existing:
        raise HTTPException(status_code=400, detail="Registration fee with this ID already exists")
    
    db_fee = RegistrationFeeDefinition(
        **fee.model_dump(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(db_fee)
    session.commit()
    session.refresh(db_fee)
    return db_fee

@app.put("/registration-fees/{fee_id}", response_model=RegistrationFeeDefinition)
def update_registration_fee(
    fee_id: str, 
    updated_fee: RegistrationFeeDefinitionUpdate, 
    session: Session = Depends(get_session)
):
    """Update a registration fee definition"""
    fee = session.get(RegistrationFeeDefinition, fee_id)
    if not fee:
        raise HTTPException(status_code=404, detail="Registration fee not found")
    
    update_data = updated_fee.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(fee, field, value)
    
    fee.updated_at = datetime.utcnow()
    session.add(fee)
    session.commit()
    session.refresh(fee)
    return fee

@app.delete("/registration-fees/{fee_id}")
def delete_registration_fee(fee_id: str, session: Session = Depends(get_session)):
    """Delete a registration fee definition"""
    fee = session.get(RegistrationFeeDefinition, fee_id)
    if not fee:
        raise HTTPException(status_code=404, detail="Registration fee not found")
    session.delete(fee)
    session.commit()
    return {"detail": "Registration fee deleted successfully"}

# ==================== Stamp Fee Tiers Endpoints ====================

@app.get("/stamp-fee-tiers", response_model=AllStampFeeTiersResponse)
def get_all_stamp_fee_tiers(session: Session = Depends(get_session)):
    """Get all stamp fee tiers grouped by transaction type"""
    tiers = session.exec(
        select(StampFeeTierDefinition).where(StampFeeTierDefinition.is_active == True)
    ).all()
    
    tiers_by_type: dict[str, List[StampFeeTier]] = {}
    default_tiers: List[StampFeeTier] = []
    
    for tier in tiers:
        tier_obj = StampFeeTier(
            min_amount=tier.min_amount,
            max_amount=tier.max_amount,
            percentage=tier.percentage
        )
        
        if tier.transaction_type == "Default":
            default_tiers.append(tier_obj)
        else:
            if tier.transaction_type not in tiers_by_type:
                tiers_by_type[tier.transaction_type] = []
            tiers_by_type[tier.transaction_type].append(tier_obj)
    
    # Sort tiers by min_amount
    for tx_type in tiers_by_type:
        tiers_by_type[tx_type].sort(key=lambda x: x.min_amount)
    default_tiers.sort(key=lambda x: x.min_amount)
    
    return AllStampFeeTiersResponse(
        tiers_by_type=tiers_by_type,
        default_tiers=default_tiers
    )

@app.get("/stamp-fee-tiers/{transaction_type}", response_model=StampFeeTiersResponse)
def get_stamp_fee_tiers_by_type(
    transaction_type: str,
    session: Session = Depends(get_session)
):
    """Get stamp fee tiers for a specific transaction type"""
    tiers = session.exec(
        select(StampFeeTierDefinition).where(
            StampFeeTierDefinition.transaction_type == transaction_type,
            StampFeeTierDefinition.is_active == True
        )
    ).all()
    
    if not tiers:
        # Fallback to default tiers
        tiers = session.exec(
            select(StampFeeTierDefinition).where(
                StampFeeTierDefinition.transaction_type == "Default",
                StampFeeTierDefinition.is_active == True
            )
        ).all()
        transaction_type = "Default"
    
    tier_list = [
        StampFeeTier(
            min_amount=tier.min_amount,
            max_amount=tier.max_amount,
            percentage=tier.percentage
        )
        for tier in sorted(tiers, key=lambda x: x.min_amount)
    ]
    
    return StampFeeTiersResponse(
        transaction_type=transaction_type,
        tiers=tier_list
    )

@app.get("/stamp-fee-tiers/all", response_model=List[StampFeeTierDefinition])
def get_all_stamp_fee_tier_definitions(session: Session = Depends(get_session)):
    """Get all stamp fee tier definitions (including inactive)"""
    tiers = session.exec(select(StampFeeTierDefinition)).all()
    return list(tiers)

@app.get("/stamp-fee-tiers/tier/{tier_id}", response_model=StampFeeTierDefinition)
def get_stamp_fee_tier(tier_id: int, session: Session = Depends(get_session)):
    """Get a specific stamp fee tier by ID"""
    tier = session.get(StampFeeTierDefinition, tier_id)
    if not tier:
        raise HTTPException(status_code=404, detail="Stamp fee tier not found")
    return tier

@app.post("/stamp-fee-tiers", response_model=StampFeeTierDefinition)
def create_stamp_fee_tier(tier: StampFeeTierDefinitionCreate, session: Session = Depends(get_session)):
    """Create a new stamp fee tier definition"""
    db_tier = StampFeeTierDefinition(
        **tier.model_dump(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(db_tier)
    session.commit()
    session.refresh(db_tier)
    return db_tier

@app.put("/stamp-fee-tiers/tier/{tier_id}", response_model=StampFeeTierDefinition)
def update_stamp_fee_tier(
    tier_id: int,
    updated_tier: StampFeeTierDefinitionUpdate,
    session: Session = Depends(get_session)
):
    """Update a stamp fee tier definition"""
    tier = session.get(StampFeeTierDefinition, tier_id)
    if not tier:
        raise HTTPException(status_code=404, detail="Stamp fee tier not found")
    
    update_data = updated_tier.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tier, field, value)
    
    tier.updated_at = datetime.utcnow()
    session.add(tier)
    session.commit()
    session.refresh(tier)
    return tier

@app.delete("/stamp-fee-tiers/tier/{tier_id}")
def delete_stamp_fee_tier(tier_id: int, session: Session = Depends(get_session)):
    """Delete a stamp fee tier definition"""
    tier = session.get(StampFeeTierDefinition, tier_id)
    if not tier:
        raise HTTPException(status_code=404, detail="Stamp fee tier not found")
    session.delete(tier)
    session.commit()
    return {"detail": "Stamp fee tier deleted successfully"}

# ==================== Utility Endpoints ====================

@app.post("/calculate-stamp-fee", response_model=CalculateStampFeeResponse)
def calculate_stamp_fee(
    request: CalculateStampFeeRequest,
    session: Session = Depends(get_session)
):
    """Calculate stamp fee percentage and amount for a given transaction"""
    transaction_type = request.transaction_type or "Default"
    
    # Get tiers for the transaction type
    tiers = session.exec(
        select(StampFeeTierDefinition).where(
            StampFeeTierDefinition.transaction_type == transaction_type,
            StampFeeTierDefinition.is_active == True
        )
    ).all()
    
    # If no tiers found for this type, use default
    if not tiers:
        tiers = session.exec(
            select(StampFeeTierDefinition).where(
                StampFeeTierDefinition.transaction_type == "Default",
                StampFeeTierDefinition.is_active == True
            )
        ).all()
        transaction_type = "Default"
    
    # Sort tiers by min_amount
    tiers = sorted(tiers, key=lambda x: x.min_amount)
    
    # Find the appropriate tier
    percentage = 2.0  # Default percentage
    tier_applied = None
    
    for tier in tiers:
        if request.amount_in_eth >= tier.min_amount:
            if tier.max_amount is None or request.amount_in_eth < tier.max_amount:
                percentage = tier.percentage
                tier_applied = StampFeeTier(
                    min_amount=tier.min_amount,
                    max_amount=tier.max_amount,
                    percentage=tier.percentage
                )
                break
    
    fee_amount = request.amount_in_eth * (percentage / 100)
    
    return CalculateStampFeeResponse(
        percentage=percentage,
        fee_amount=fee_amount,
        transaction_type=transaction_type,
        tier_applied=tier_applied
    )

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "definitions-service"}

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "DeedLink Definitions Service",
        "version": "1.0.0",
        "endpoints": {
            "registration_fees": "/registration-fees",
            "stamp_fee_tiers": "/stamp-fee-tiers",
            "calculate_stamp_fee": "/calculate-stamp-fee",
            "health": "/health"
        }
    }
