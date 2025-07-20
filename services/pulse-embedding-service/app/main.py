from fastapi import FastAPI, BackgroundTasks
from .embedding_logic import generate_and_update_embeddings

app = FastAPI(title="Pulse Embedding Service")

@app.post("/run-batch")
async def run_batch_job(background_tasks: BackgroundTasks):
    """
    Triggers the embedding generation process in the background.
    """
    print("API: Received request to run embedding batch job.")
    background_tasks.add_task(generate_and_update_embeddings)
    return {"status": "success", "message": "Embedding job started in the background."}