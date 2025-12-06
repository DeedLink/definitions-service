from sqlmodel import SQLModel, Field

class PaymentRule(SQLModel, table=True):
    id: str = Field(primary_key=True)
    type: str  # "percentage" or "fixed"
    value: float
