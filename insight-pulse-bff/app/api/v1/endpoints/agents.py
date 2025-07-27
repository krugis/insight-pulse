from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any # Ensure Dict and Any are imported
from datetime import datetime, timedelta, UTC # For mock data in get_agent_runs

from app.api.v1.deps import get_db_session, get_current_user
from app.models.user import User
from app.crud import agent as crud_agent
from app.schemas.agent import AgentCreate, AgentResponse, AgentStatusUpdate, AgentRun, AgentUpdate 
from app.services.pulse_agent_manager_client import pulse_agent_manager_client

router = APIRouter()

@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED, tags=["Agents"])
async def create_ai_agent(
    agent_in: AgentCreate, # Incoming payload from frontend matches this schema
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Create a new AI agent for the authenticated user.
    Interacts with the external pulse-agent-manager service.
    """
    # Prepare API keys based on plan
    apify_key = agent_in.apify_token if agent_in.plan == "byok" else None
    openai_key = agent_in.openai_token if agent_in.plan == "byok" else None

    # 1. Prepare payload for external pulse-agent-manager
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
    config_data_for_bff_db = {
        "plan": agent_in.plan,
        "linkedin_urls": agent_in.linkedin_urls,
        "digest_tone": agent_in.digest_tone,
        "post_tone": agent_in.post_tone,
    }

    db_agent = crud_agent.create_agent(
        db=db,
        user_id=current_user.id,
        agent_name=agent_in.agent_name,
        pulse_agent_manager_id=pulse_agent_manager_id,
        config_data=config_data_for_bff_db,
        apify_token=apify_key,
        openai_token=openai_key
    )
    
    return db_agent

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

@router.get("/{agent_id}", response_model=AgentResponse, tags=["Agents"])
async def get_single_agent(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve details for a specific AI agent by its ID.
    """
    agent = crud_agent.get_agent(db, agent_id, current_user.id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent

@router.patch("/{agent_id}/status", response_model=AgentResponse, tags=["Agents"])
async def update_agent_status(
    agent_id: int,
    status_update: AgentStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Update the status (e.g., pause, activate) of an AI agent.
    Interacts with the external pulse-agent-manager service.
    """
    db_agent = crud_agent.get_agent(db, agent_id, current_user.id)
    if not db_agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    try:
        await pulse_agent_manager_client.update_remote_agent_status(
            agent_id=db_agent.pulse_agent_manager_id,
            new_status=status_update.status
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to update status with external manager: {e}"
        )
    
    updated_agent = crud_agent.update_agent_status(
        db=db, 
        agent_id=agent_id, 
        user_id=current_user.id, 
        new_status=status_update.status
    )
    return updated_agent

@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Agents"])
async def delete_ai_agent(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Delete an AI agent.
    Interacts with the external pulse-agent-manager service.
    """
    db_agent = crud_agent.get_agent(db, agent_id, current_user.id)
    if not db_agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    try:
        await pulse_agent_manager_client.delete_remote_agent(
            agent_id=db_agent.pulse_agent_manager_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to delete agent with external manager: {e}"
        )

    success = crud_agent.delete_agent(db, agent_id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete agent from BFF DB")

@router.get("/{agent_id}/runs", response_model=List[AgentRun], tags=["Agents"])
async def get_agent_runs(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve historical runs for a specific agent.
    (Mocks data for now; in production, this would call a downstream service
    like a 'pulse-runs-api' or query run logs.)
    """
    # First, ensure the agent belongs to the current user
    agent = crud_agent.get_agent(db, agent_id, current_user.id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found for this user.")

    # --- MOCK DATA GENERATION ---
    mock_runs = [
        AgentRun(
            run_id=f"run_{agent_id}_001",
            agent_id=agent_id,
            timestamp=datetime.now(UTC) - timedelta(days=1, hours=2),
            status="completed",
            output_summary="Successfully processed 5 LinkedIn posts. Digest and summary email sent.",
            generated_digest_url="https://example.com/digest/agent_id_001.pdf",
            generated_post_url="https://linkedin.com/post/agent_id_001"
        ),
        AgentRun(
            run_id=f"run_{agent_id}_002",
            agent_id=agent_id,
            timestamp=datetime.now(UTC) - timedelta(hours=8),
            status="completed",
            output_summary="Processed 7 LinkedIn posts. Content generated and email sent.",
            generated_digest_url="https://example.com/digest/agent_id_002.pdf",
            generated_post_url="https://linkedin.com/post/agent_id_002"
        ),
        AgentRun(
            run_id=f"run_{agent_id}_003",
            agent_id=agent_id,
            timestamp=datetime.now(UTC) - timedelta(hours=2),
            status="failed",
            output_summary="Failed to connect to Apify API for scraping. Review API key.",
            generated_digest_url=None,
            generated_post_url=None
        )
    ]
    # END MOCK DATA
    return mock_runs

@router.patch("/{agent_id}", response_model=AgentResponse, tags=["Agents"])
async def update_agent_details(
    agent_id: int,
    agent_update: AgentUpdate, # Incoming payload for update
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Update details of an existing AI agent (name, URLs, tones, API keys).
    Interacts with the external pulse-agent-manager service.
    """
    db_agent = crud_agent.get_agent(db, agent_id, current_user.id)
    if not db_agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found.")

    # Prepare data for pulse-agent-manager
    update_data_for_remote = agent_update.model_dump(exclude_unset=True)

    # Transform keys to camelCase for pulse-agent-manager where applicable
    remote_update_payload = {}
    for key, value in update_data_for_remote.items():
        if key == "linkedin_urls": remote_update_payload["linkedinUrls"] = value
        elif key == "digest_tone": remote_update_payload["digestTone"] = value
        elif key == "post_tone": remote_update_payload["postTone"] = value
        elif key == "apify_token": remote_update_payload["apifyToken"] = value
        elif key == "openai_token": remote_update_payload["openaiToken"] = value
        else: remote_update_payload[key] = value

    if db_agent.config_data.get("plan") == "byok":
        if "plan" in remote_update_payload and remote_update_payload["plan"] == "byok":
            if not remote_update_payload.get("apifyToken") or not remote_update_payload.get("openaiToken"):
                raise HTTPException(status_code=400, detail="API tokens are required for BYOK plan.")


    try:
        if remote_update_payload:
            await pulse_agent_manager_client.update_remote_agent(
                agent_id=db_agent.pulse_agent_manager_id,
                update_data=remote_update_payload
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to update agent with external manager: {e}"
        )

    # Update agent details in BFF's database
    # REMOVE THESE LINES -- THE CRUD FUNCTION HANDLES ALL DB UPDATES NOW
    # if "linkedin_urls" in update_data_for_remote: db_agent.config_data["linkedin_urls"] = update_data_for_remote["linkedin_urls"]
    # if "digest_tone" in update_data_for_remote: db_agent.config_data["digest_tone"] = update_data_for_remote["digest_tone"]
    # if "post_tone" in update_data_for_remote: db_agent.config_data["post_tone"] = update_data_for_remote["post_tone"]
    # if "plan" in update_data_for_remote: db_agent.config_data["plan"] = update_data_for_remote["plan"]

    # Call CRUD function to handle all database modifications
    updated_agent = crud_agent.update_agent(
        db=db,
        agent_id=agent_id,
        user_id=current_user.id,
        agent_update_data=agent_update.model_dump(exclude_unset=True) # Pass the Pydantic dict directly
    )
    return updated_agent
    
    return mock_runs