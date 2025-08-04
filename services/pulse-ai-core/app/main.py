from fastapi import FastAPI, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from datetime import date
from . import newspaper_generator, topic_post_generator, analyzer
from .db import models, database, schemas

# Create DB tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Pulse AI Core Service")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_and_save_digest(db: Session):
    """The background task that runs the full AI pipeline."""
    content = newspaper_generator.generate_newspaper_content()
    if content:
        today = date.today()
        # Check if a digest for today already exists
        db_digest = db.query(models.DailyDigest).filter(models.DailyDigest.publication_date == today).first()
        if not db_digest:
            db_digest = models.DailyDigest(publication_date=today, content_json=content)
            db.add(db_digest)
            db.commit()
            print(f"✅ Digest for {today} saved to database.")
        else:
            print(f"Digest for {today} already exists. Skipping save.")

@app.post("/generate-newspaper", response_model=schemas.DigestResponse)
async def generate_newspaper_endpoint(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Triggers the newspaper generation and saves the result to the database.
    """
    background_tasks.add_task(create_and_save_digest, db)
    return {"status": "success", "message": "Newspaper generation job started in the background."}

@app.get("/docs")
def read_docs():
    return {"message": "API Documentation"}