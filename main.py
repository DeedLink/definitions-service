from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from sqlmodel import Session, select
from models import PaymentRule, PaymentRuleCreate, PaymentRuleUpdate
from database import engine, create_db_and_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db_and_tables()
    yield
    # Shutdown (if needed)

app = FastAPI(title="Payment Rules CRUD API", lifespan=lifespan)

# Get all payment rules
@app.get("/payment-rules", response_model=list[PaymentRule])
def get_rules():
    with Session(engine) as session:
        rules = session.exec(select(PaymentRule)).all()
        return rules

# Get single payment rule by ID
@app.get("/payment-rules/{rule_id}", response_model=PaymentRule)
def get_rule(rule_id: str):
    with Session(engine) as session:
        rule = session.get(PaymentRule, rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        return rule

# Create a new payment rule
@app.post("/payment-rules", response_model=PaymentRule)
def create_rule(rule: PaymentRuleCreate):
    with Session(engine) as session:
        existing = session.get(PaymentRule, rule.id)
        if existing:
            raise HTTPException(status_code=400, detail="Rule already exists")
        db_rule = PaymentRule(**rule.model_dump())
        session.add(db_rule)
        session.commit()
        session.refresh(db_rule)
        return db_rule

# Update an existing payment rule
@app.put("/payment-rules/{rule_id}", response_model=PaymentRule)
def update_rule(rule_id: str, updated_rule: PaymentRuleUpdate):
    with Session(engine) as session:
        rule = session.get(PaymentRule, rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        update_data = updated_rule.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(rule, field, value)
        session.add(rule)
        session.commit()
        session.refresh(rule)
        return rule

# Delete a payment rule
@app.delete("/payment-rules/{rule_id}")
def delete_rule(rule_id: str):
    with Session(engine) as session:
        rule = session.get(PaymentRule, rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        session.delete(rule)
        session.commit()
        return {"detail": "Rule deleted successfully"}
