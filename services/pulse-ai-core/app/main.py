from fastapi import FastAPI, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from datetime import date
from pydantic import BaseModel, Field 
from typing import Literal
from . import newspaper_generator, topic_post_generator, analyzer
from .db import models, database, schemas

class AnalysisRequest(BaseModel):
    days_back: int = Field(1, ge=1, le=30)
    algorithm: Literal['hdbscan', 'bertopic'] = 'hdbscan'

# Create DB tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Pulse AI Core Service")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_and_save_digest(db: Session, request_params: AnalysisRequest):
    """The background task that runs the full AI pipeline with parameters."""
    content = newspaper_generator.generate_newspaper_content(
        days_back=request_params.days_back,
        algorithm=request_params.algorithm
    )
    if content:
        today = date.today()
        db_digest = db.query(models.DailyDigest).filter(models.DailyDigest.publication_date == today).first()
        if not db_digest:
            db_digest = models.DailyDigest(publication_date=today, content_json=content)
            db.add(db_digest)
            db.commit()
            print(f"✅ Digest for {today} saved to database.")
        else:
            print(f"Digest for {today} already exists. Skipping save.")

@app.post("/generate-newspaper", response_model=schemas.JobSubmissionResponse)
async def generate_newspaper_endpoint(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    """
    Triggers newspaper generation with configurable parameters.
    """
    background_tasks.add_task(create_and_save_digest, db, request)
    return {"status": "success", "message": "Newspaper generation job started."}

@app.get("/docs")
def read_docs():
    return {"message": "API Documentation"}