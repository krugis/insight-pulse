from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create FastAPI app instance
app = FastAPI(
    title="Insight Pulse BFF",
    description="Backend-for-Frontend for AIGORA's AI Agent Management",
    version="0.1.0",
)

# Configure CORS (Cross-Origin Resource Sharing)
# This allows your frontend (running on a different origin) to communicate with this BFF.
# Adjust origins in production to be more restrictive.
origins = [
    "http://localhost",
    "http://localhost:8000", # Example for Uvicorn
    "http://localhost:8080", # Example for frontend development server
    "http://127.0.0.1:8000",
    "http://127.0.0.1:5500", # Common for Live Server VS Code extension
    "https://aigora.cloud", # Your production frontend domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers here (will add in subsequent steps)
# from app.api.v1.api import api_router
# app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Insight Pulse BFF is running!"}

# You can add more global event handlers here if needed
@app.on_event("startup")
async def startup_event():
    print("Insight Pulse BFF starting up...")
    # Placeholder for any database migration or initial setup logic
    # You'll run initial_db_setup.py script separately for table creation
    pass

@app.on_event("shutdown")
async def shutdown_event():
    print("Insight Pulse BFF shutting down...")
    pass