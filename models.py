from sqlmodel import SQLModel, Field

class PaymentRule(SQLModel, table=True):
    id: str = Field(primary_key=True)
    type: str  # "percentage" or "fixed"
    value: float

# Request/Response models
class PaymentRuleCreate(SQLModel):
    id: str
    type: str
    value: float

class PaymentRuleUpdate(SQLModel):
    type: str | None = None
    value: float | None = None
