from fastapi import FastAPI, HTTPException
from sqlmodel import Session, select
from models import PaymentRule
from database import engine, create_db_and_tables

app = FastAPI(title="Payment Rules CRUD API")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Get all payment rules
@app.get("/payment-rules")
def get_rules():
    with Session(engine) as session:
        rules = session.exec(select(PaymentRule)).all()
        return rules

# Get single payment rule by ID
@app.get("/payment-rules/{rule_id}")
def get_rule(rule_id: str):
    with Session(engine) as session:
        rule = session.get(PaymentRule, rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        return rule

# Create a new payment rule
@app.post("/payment-rules")
def create_rule(rule: PaymentRule):
    with Session(engine) as session:
        existing = session.get(PaymentRule, rule.id)
        if existing:
            raise HTTPException(status_code=400, detail="Rule already exists")
        session.add(rule)
        session.commit()
        return rule

# Update an existing payment rule
@app.put("/payment-rules/{rule_id}")
def update_rule(rule_id: str, updated_rule: PaymentRule):
    with Session(engine) as session:
        rule = session.get(PaymentRule, rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        rule.type = updated_rule.type
        rule.value = updated_rule.value
        session.add(rule)
        session.commit()
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
