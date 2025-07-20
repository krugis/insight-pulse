from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import schemas
from .db import models, database

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Pulse Agent Manager")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/agents/", response_model=schemas.AgentResponse)
def create_agent(agent_data: schemas.AgentCreate, db: Session = Depends(get_db)):
    db_agent = db.query(models.Agent).filter(models.Agent.email == agent_data.email).first()
    if db_agent:
        raise HTTPException(status_code=400, detail="An agent with this email already exists.")

    new_agent = models.Agent(
        email=agent_data.email,
        plan_type=agent_data.plan_type,
        encrypted_apify_token=agent_data.apify_token,
        encrypted_openai_token=agent_data.openai_token,
        preferences={
            "digest_tone": agent_data.digest_tone,
            "post_tone": agent_data.post_tone
        }
    )

    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)

    for url in agent_data.linkedin_urls:
        new_profile = models.Profile(url=str(url), agent_id=new_agent.id)
        db.add(new_profile)

    db.commit()

    return schemas.AgentResponse.from_orm(new_agent)