from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentStatusUpdate

def create_agent(
    db: Session, 
    user_id: int,
    agent_name: str,
    pulse_agent_manager_id: str,
    config_data: Dict[str, Any], 
    apify_token: Optional[str] = None,
    openai_token: Optional[str] = None
) -> Agent:
    db_agent = Agent(
        user_id=user_id,
        agent_name=agent_name,
        pulse_agent_manager_id=pulse_agent_manager_id,
        config_data=config_data,
        apify_token=apify_token,
        openai_token=openai_token
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent

def get_agent(db: Session, agent_id: int, user_id: int) -> Optional[Agent]:
    return db.query(Agent).filter(Agent.id == agent_id, Agent.user_id == user_id).first()

def get_user_agents(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Agent]:
    return db.query(Agent).filter(Agent.user_id == user_id).offset(skip).limit(limit).all()

def update_agent_status(db: Session, agent_id: int, user_id: int, new_status: str) -> Optional[Agent]:
    db_agent = get_agent(db, agent_id, user_id)
    if db_agent:
        db_agent.status = new_status
        db.commit()
        db.refresh(db_agent)
    return db_agent

def delete_agent(db: Session, agent_id: int, user_id: int) -> bool:
    db_agent = get_agent(db, agent_id, user_id)
    if db_agent:
        db.delete(db_agent)
        db.commit()
        return True
    return False

def update_agent(
    db: Session,
    agent_id: int, # ID of the agent to update
    user_id: int,  # User ID for ownership check
    agent_update_data: Dict[str, Any] # Dictionary of fields to update (from agent_update.model_dump())
) -> Optional[Agent]:
    db_agent = get_agent(db, agent_id, user_id) # Retrieve the agent
    if db_agent:
        # Ensure config_data is a dictionary (it's JSON type, so it should be a dict)
        # This handles case where config_data might be None if Agent was created unusually
        if db_agent.config_data is None:
            db_agent.config_data = {}

        # Iterate through the incoming update data
        for key, value in agent_update_data.items():
            # Direct fields on the Agent model
            if key == "agent_name":
                db_agent.agent_name = value
            elif key == "status":
                db_agent.status = value
            elif key == "apify_token":
                db_agent.apify_token = value
            elif key == "openai_token":
                db_agent.openai_token = value
            # Fields that belong inside the config_data dictionary
            elif key in ["linkedin_urls", "digest_tone", "post_tone", "plan"]: # 'plan' is in config_data too
                db_agent.config_data[key] = value
            # Add more elifs for other direct fields if your Agent model grows

        # IMPORTANT FOR SQLAlchemy JSON type:
        # If you modify a JSON column's dictionary in place, SQLAlchemy might not
        # detect the change. Reassigning it forces SQLAlchemy to mark it as dirty.
        db_agent.config_data = dict(db_agent.config_data) 

        db.add(db_agent) # Ensure the object is tracked by the session
        db.commit()      # Persist changes to the database
        db.refresh(db_agent) # Refresh the object to get its latest state from the DB

    return db_agent