from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import schemas
from .db import models, database

# Create all database tables on startup
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Pulse Agent Manager")

# Dependency to get a DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/agents/", response_model=schemas.Agent)
def create_agent(agent: schemas.AgentCreate, db: Session = Depends(get_db)):
    """
    Creates a new agent configuration in the database.
    """
    db_agent = db.query(models.Agent).filter(models.Agent.email == agent.email).first()
    if db_agent:
        raise HTTPException(status_code=400, detail="Email already registered")

    # TODO: Encrypt tokens before saving
    new_agent = models.Agent(
        email=agent.email,
        plan_type=agent.plan_type,
        encrypted_apify_token=agent.apify_token, # Placeholder
        encrypted_openai_token=agent.openai_token, # Placeholder
        preferences={
            "digest_tone": agent.digest_tone,
            "post_tone": agent.post_tone
        }
    )
    
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)

    # Add profiles
    for url in agent.linkedin_urls:
        new_profile = models.Profile(url=str(url), agent_id=new_agent.id)
        db.add(new_profile)
    
    db.commit()
    
    # To return the full agent object, we need to manually construct it
    # This is a simplification for now.
    return schemas.Agent(
        id=new_agent.id,
        email=new_agent.email,
        plan_type=new_agent.plan_type,
        digest_tone=agent.digest_tone,
        post_tone=agent.post_tone,
        linkedin_urls=agent.linkedin_urls
    )