from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.v1.deps import get_db_session, get_current_user
from app.models.user import User
from app.crud import agent as crud_agent
from app.schemas.agent import AgentCreate, AgentResponse, AgentStatusUpdate, AgentRun
from app.services.pulse_agent_manager_client import pulse_agent_manager_client

from datetime import datetime, timedelta, UTC

router = APIRouter()

@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED, tags=["Agents"])
async def create_ai_agent(
    agent_in: AgentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    # 1. Prepare data for external pulse-agent-manager
    remote_config_data = {
        "linkedin_urls": agent_in.linkedin_urls,
        "digest_tone": agent_in.digest_tone,
        "post_tone": agent_in.post_tone,
    }
    
    apify_key = agent_in.apify_token if agent_in.plan == "byok" else None
    openai_key = agent_in.openai_token if agent_in.plan == "byok" else None

    # 2. Call the external pulse-agent-manager to create the agent
    try:
        remote_agent_response = await pulse_agent_manager_client.create_remote_agent(
            user_id=current_user.id,
            agent_name=agent_in.agent_name,
            config_data=remote_config_data,
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
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to create agent with external manager: {e}"
        )

    # 3. Store agent details in BFF's database
    db_agent = crud_agent.create_agent(
        db=db,
        user_id=current_user.id,
        agent_name=agent_in.agent_name,
        pulse_agent_manager_id=pulse_agent_manager_id,
        config_data={
            "plan": agent_in.plan,
            "linkedin_urls": agent_in.linkedin_urls,
            "digest_tone": agent_in.digest_tone,
            "post_tone": agent_in.post_tone,
        },
        apify_token=apify_key,
        openai_token=openai_key
    )
    
    return db_agent

@router.get("/", response_model=List[AgentResponse], tags=["Agents"])
async def get_all_agents_for_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    agents = crud_agent.get_user_agents(db, user_id=current_user.id)
    return agents

@router.get("/{agent_id}", response_model=AgentResponse, tags=["Agents"])
async def get_single_agent(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
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

    # First, ensure the agent belongs to the current user
    agent = crud_agent.get_agent(db, agent_id, current_user.id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found for this user.")

    # --- MOCK DATA GENERATION ---
    # This is placeholder data. In a real system, you would:
    # 1. Call a dedicated backend service (e.g., 'pulse-runs-api')
    #    Example: remote_runs_data = await pulse_runs_api_client.get_runs(agent_id=agent.pulse_agent_manager_id)
    # 2. Transform that data into AgentRun schemas.

    mock_runs = [
        AgentRun(
            run_id=f"run_{agent_id}_001",
            agent_id=agent_id,
            timestamp=datetime.now(UTC) - timedelta(days=1, hours=2), # Example timestamp
            status="completed",
            output_summary="Successfully processed 5 LinkedIn posts. Digest and summary email sent.",
            generated_digest_url="https://example.com/digest/agent_id_001.pdf",
            generated_post_url="https://linkedin.com/post/agent_id_001"
        ),
        AgentRun(
            run_id=f"run_{agent_id}_002",
            agent_id=agent_id,
            timestamp=datetime.now(UTC) - timedelta(hours=8), # Example timestamp
            status="completed",
            output_summary="Processed 7 LinkedIn posts. Content generated and email sent.",
            generated_digest_url="https://example.com/digest/agent_id_002.pdf",
            generated_post_url="https://linkedin.com/post/agent_id_002"
        ),
        AgentRun(
            run_id=f"run_{agent_id}_003",
            agent_id=agent_id,
            timestamp=datetime.now(UTC) - timedelta(hours=2), # Example timestamp
            status="failed",
            output_summary="Failed to connect to Apify API for scraping. Review API key.",
            generated_digest_url=None,
            generated_post_url=None
        )
    ]
    # END MOCK DATA

    return mock_runs