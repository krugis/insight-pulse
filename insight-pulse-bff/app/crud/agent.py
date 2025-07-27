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

def update_agent(db: Session, agent_id: int, user_id: int, agent_update_data: Dict[str, Any]) -> Optional[Agent]:
    db_agent = get_agent(db, agent_id, user_id)
    if db_agent:
        # Update fields from agent_update_data
        for key, value in agent_update_data.items():
            if hasattr(db_agent, key):
                # Handle config_data separately if it's a nested update
                if key == "config_data" and isinstance(value, dict):
                    db_agent.config_data.update(value) # Merge updates into existing config_data
                else:
                    setattr(db_agent, key, value)

        db.add(db_agent) # Ensure it's tracked by the session
        db.commit()
        db.refresh(db_agent)
    return db_agent