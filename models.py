from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer
from typing import Optional, List
from datetime import datetime

# Registration Fee Definition Model
class RegistrationFeeDefinition(SQLModel, table=True):
    __tablename__ = "registration_fee_definitions"
    
    id: str = Field(primary_key=True, description="Unique identifier (e.g., 'government_fee', 'ivsl_fee')")
    name: str = Field(description="Fee name (e.g., 'Government Fee', 'IVSL Fee')")
    value: float = Field(description="Fee value in ETH")
    description: Optional[str] = Field(default=None, description="Optional description")
    is_active: bool = Field(default=True, description="Whether this fee is currently active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Stamp Fee Tier Definition Model
class StampFeeTierDefinition(SQLModel, table=True):
    __tablename__ = "stamp_fee_tier_definitions"
    
    id: Optional[int] = Field(default=None, primary_key=True, sa_column=Column(Integer, autoincrement=True))
    transaction_type: str = Field(description="Transaction type (e.g., 'Sale', 'Gift', 'Transfer', 'Exchange', 'Lease', 'Mortgage', 'Default')")
    min_amount: float = Field(description="Minimum amount in ETH (inclusive)")
    max_amount: Optional[float] = Field(default=None, description="Maximum amount in ETH (exclusive, None means Infinity)")
    percentage: float = Field(description="Stamp fee percentage for this tier")
    is_active: bool = Field(default=True, description="Whether this tier is currently active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Request/Response Models
class RegistrationFeeDefinitionCreate(SQLModel):
    id: str
    name: str
    value: float
    description: Optional[str] = None
    is_active: bool = True

class RegistrationFeeDefinitionUpdate(SQLModel):
    name: Optional[str] = None
    value: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class StampFeeTierDefinitionCreate(SQLModel):
    transaction_type: str
    min_amount: float
    max_amount: Optional[float] = None
    percentage: float
    is_active: bool = True

class StampFeeTierDefinitionUpdate(SQLModel):
    transaction_type: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    percentage: Optional[float] = None
    is_active: Optional[bool] = None

# Response Models for API
class RegistrationFeesResponse(SQLModel):
    government_fee: float
    ivsl_fee: float
    survey_fee: float
    notary_fee: float
    total_registration_fee: float

class StampFeeTier(SQLModel):
    min_amount: float
    max_amount: Optional[float]
    percentage: float

class StampFeeTiersResponse(SQLModel):
    transaction_type: str
    tiers: List[StampFeeTier]

class AllStampFeeTiersResponse(SQLModel):
    tiers_by_type: dict[str, List[StampFeeTier]]
    default_tiers: List[StampFeeTier]

class CalculateStampFeeRequest(SQLModel):
    amount_in_eth: float
    transaction_type: Optional[str] = None

class CalculateStampFeeResponse(SQLModel):
    percentage: float
    fee_amount: float
    transaction_type: str
    tier_applied: Optional[StampFeeTier] = None
