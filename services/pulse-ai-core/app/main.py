from fastapi import FastAPI, HTTPException, BackgroundTasks
from . import newspaper_generator, topic_post_generator, analyzer

app = FastAPI(title="Pulse AI Core Service")

@app.post("/generate-for-agent/{agent_id}")
async def generate_content_for_agent(agent_id: int, background_tasks: BackgroundTasks):
    """
    Triggers the full analysis and content generation pipeline for a single agent.
    This is the endpoint the scheduler will call for each user.
    """
    # In a real app, you would fetch the agent's config from pulse-agent-manager
    # For now, we'll just log the ID
    print(f"--- Triggered AI Core for Agent ID: {agent_id} ---")

    # Run the generation scripts in the background so the API can respond immediately
    background_tasks.add_task(newspaper_generator.generate_newspaper_content)
    background_tasks.add_task(topic_post_generator.generate_topic_post)
    
    return {"status": "success", "message": f"AI Core tasks scheduled for agent {agent_id}"}