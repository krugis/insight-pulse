from sqlalchemy.orm import Session
from sqlalchemy import text
from dotenv import load_dotenv

from app.core.database import engine, Base, SessionLocal
from app.models import user, agent # NEW: Import agent model
from app.core.config import settings
import time

def create_db_and_tables():
    print("Attempting to connect to the database and create tables...")
    max_retries = 10
    for i in range(max_retries):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            print("Database connection successful.")
            Base.metadata.create_all(bind=engine) # This will now create tables for User and Agent
            print("Database tables created (or already exist).")
            break
        except Exception as e:
            print(f"Database connection failed (Attempt {i+1}/{max_retries}): {e}")
            time.sleep(5)
    else:
        print("Failed to connect to the database after multiple retries. Exiting.")
        exit(1)

if __name__ == "__main__":
    load_dotenv()
    print(f"Using DATABASE_URL: {settings.DATABASE_URL}")
    create_db_and_tables()