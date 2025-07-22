# In app/api/v1/endpoints/agents.py
# ... (imports) ...

@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED, tags=["Agents"])
async def create_ai_agent(
    agent_in: AgentCreate, # This is the incoming data from frontend/curl
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    # Prepare API keys based on plan
    apify_key = agent_in.apify_token if agent_in.plan == "byok" else None
    openai_key = agent_in.openai_token if agent_in.plan == "byok" else None

    # Call the external pulse-agent-manager to create the agent
    try:
        remote_agent_response = await pulse_agent_manager_client.create_remote_agent(
            user_id=current_user.id, # Still passed for context in BFF's client
            agent_name=agent_in.agent_name, # Still passed for context in BFF's client
            # NEW: Pass these parameters directly from agent_in
            email=agent_in.email,
            plan=agent_in.plan,
            linkedin_urls=agent_in.linkedin_urls,
            digest_tone=agent_in.digest_tone,
            post_tone=agent_in.post_tone,
            apify_token=apify_key,
            openai_token=openai_key
            # REMOVE THIS LINE: config_data={...}
        )
        # ... (rest of the try block and error handling) ...
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

    # Store agent details in BFF's database
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