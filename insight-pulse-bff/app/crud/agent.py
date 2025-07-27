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
        print(f"DEBUG CRUD: Entering update_agent for agent_id: {agent_id}, user_id: {user_id}")
        print(f"DEBUG CRUD: Initial db_agent.agent_name: {db_agent.agent_name}, config_data: {db_agent.config_data}")
        print(f"DEBUG CRUD: Incoming agent_update_data: {agent_update_data}")

        # Ensure config_data is a dictionary (it's JSON type, so it should be a dict)
        if db_agent.config_data is None:
            db_agent.config_data = {}

        # Iterate through the provided update fields in agent_update_data
        for key, value in agent_update_data.items():
            # Fields that are directly on the Agent model
            if key == "agent_name":
                db_agent.agent_name = value
                print(f"DEBUG CRUD: Updated agent_name to: {db_agent.agent_name}")
            elif key == "status": # This handles status updates if sent via this generic endpoint
                db_agent.status = value
                print(f"DEBUG CRUD: Updated status to: {db_agent.status}")
            elif key == "apify_token":
                db_agent.apify_token = value
                print(f"DEBUG CRUD: Updated apify_token (set if not None).")
            elif key == "openai_token":
                db_agent.openai_token = value
                print(f"DEBUG CRUD: Updated openai_token (set if not None).")
            # Fields that belong inside the nested config_data dictionary
            elif key in ["linkedin_urls", "digest_tone", "post_tone", "plan"]: # 'plan' is also part of config_data
                db_agent.config_data[key] = value
                print(f"DEBUG CRUD: Updated config_data['{key}'] to: {db_agent.config_data[key]}")
            else:
                # Log if there are unexpected keys in update_data, or if it's a field handled elsewhere
                print(f"DEBUG CRUD: Skipping unhandled update key (might be intentional): {key}")

        # IMPORTANT FOR SQLAlchemy JSON type:
        # If you modify a JSON column's dictionary in place, SQLAlchemy might not
        # detect the change. Reassigning it forces SQLAlchemy to mark it as dirty.
        db_agent.config_data = dict(db_agent.config_data) 
        print(f"DEBUG CRUD: config_data after in-memory update: {db_agent.config_data}")

        db.add(db_agent)      # Ensure the object is tracked by the session
        db.commit()           # Persist changes to the database
        db.refresh(db_agent) # Refresh the object to get its latest state from the DB
        print(f"DEBUG CRUD: Agent ID {agent_id} successfully committed. Final db_agent.agent_name: {db_agent.agent_name}, config_data: {db_agent.config_data}")
    else:
        print(f"DEBUG CRUD: Agent {agent_id} not found for user {user_id} in update_agent.")
    return db_agent