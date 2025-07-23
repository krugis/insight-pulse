from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, UTC

from app.api.v1.deps import get_db_session, get_current_user
from app.models.user import User
from app.crud import agent as crud_agent
from app.schemas.agent import AgentCreate, AgentResponse, AgentStatusUpdate, AgentRun
from app.services.pulse_agent_manager_client import pulse_agent_manager_client

router = APIRouter()

@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED, tags=["Agents"])
async def create_ai_agent(
    agent_in: AgentCreate, # Incoming payload from frontend matches this schema
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    # Prepare API keys based on plan
    apify_key = agent_in.apify_token if agent_in.plan == "byok" else None
    openai_key = agent_in.openai_token if agent_in.plan == "byok" else None

    # 1. Prepare payload for external pulse-agent-manager
    # (Ensure field names match pulse-agent-manager's schema - camelCase where aliased)
    remote_payload_to_pulse_agent_manager = {
        "email": agent_in.email,
        "plan": agent_in.plan,
        "linkedinUrls": agent_in.linkedin_urls, # Use camelCase as per remote's schema
        "digestTone": agent_in.digest_tone,     # Use camelCase
        "postTone": agent_in.post_tone,         # Use camelCase
        "apifyToken": apify_key,                # Use camelCase
        "openaiToken": openai_key,              # Use camelCase
    }
    # Filter out None values before sending to remote service
    remote_payload_to_pulse_agent_manager = {k: v for k, v in remote_payload_to_pulse_agent_manager.items() if v is not None}

    # 2. Call the external pulse-agent-manager to create the agent
    try:
        # Pass the direct fields here as expected by pulse_agent_manager_client.create_remote_agent
        remote_agent_response = await pulse_agent_manager_client.create_remote_agent(
            user_id=current_user.id, # For BFF's context/logging
            agent_name=agent_in.agent_name, # For BFF's context/logging
            email=agent_in.email,
            plan=agent_in.plan,
            linkedin_urls=agent_in.linkedin_urls,
            digest_tone=agent_in.digest_tone,
            post_tone=agent_in.post_tone,
            apify_token=apify_key,
            openai_token=openai_key
        )
        pulse_agent_manager_id = remote_agent_response.get("agent_id") or remote_agent_response.get("id")
        if not pulse_agent_manager_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="External agent manager did not return an agent ID."
            )

    except HTTPException:
        raise # Re-raise FastAPI HTTPExceptions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to create agent with external manager: {e}"
        )

    # 3. Store agent details in BFF's database
    # Assemble config_data explicitly from agent_in's fields for BFF's DB storage
    config_data_for_bff_db = {
        "plan": agent_in.plan,
        "linkedin_urls": agent_in.linkedin_urls,
        "digest_tone": agent_in.digest_tone,
        "post_tone": agent_in.post_tone,
        # Add any other fields from agent_in that you want to store in config_data
    }

    db_agent = crud_agent.create_agent(
        db=db,
        user_id=current_user.id,
        agent_name=agent_in.agent_name,
        pulse_agent_manager_id=pulse_agent_manager_id,
        config_data=config_data_for_bff_db, # Use the assembled config_data
        apify_token=apify_key,
        openai_token=openai_key
    )

    return db_agent # This will correctly return AgentResponse as config_data is now filled

@router.get("/", response_model=List[AgentResponse], tags=["Agents"])
async def get_all_agents_for_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve all AI agents belonging to the current authenticated user.
    """
    agents = crud_agent.get_user_agents(db, user_id=current_user.id)
    return agents