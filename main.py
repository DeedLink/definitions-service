from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Session, select
from models import PaymentRule, PaymentRuleCreate, PaymentRuleUpdate
from database import engine, create_db_and_tables

app = FastAPI(title="Payment Rules CRUD API")

def get_session():
    create_db_and_tables()
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()

@app.get("/payment-rules", response_model=list[PaymentRule])
def get_rules(session: Session = Depends(get_session)):
    rules = session.exec(select(PaymentRule)).all()
    return rules

@app.get("/payment-rules/{rule_id}", response_model=PaymentRule)
def get_rule(rule_id: str, session: Session = Depends(get_session)):
    rule = session.get(PaymentRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule

@app.post("/payment-rules", response_model=PaymentRule)
def create_rule(rule: PaymentRuleCreate, session: Session = Depends(get_session)):
    existing = session.get(PaymentRule, rule.id)
    if existing:
        raise HTTPException(status_code=400, detail="Rule already exists")
    db_rule = PaymentRule(**rule.model_dump())
    session.add(db_rule)
    session.commit()
    session.refresh(db_rule)
    return db_rule

@app.put("/payment-rules/{rule_id}", response_model=PaymentRule)
def update_rule(rule_id: str, updated_rule: PaymentRuleUpdate, session: Session = Depends(get_session)):
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

@app.delete("/payment-rules/{rule_id}")
def delete_rule(rule_id: str, session: Session = Depends(get_session)):
    rule = session.get(PaymentRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    session.delete(rule)
    session.commit()
    return {"detail": "Rule deleted successfully"}
