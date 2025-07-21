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
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:8080",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:5500",
    "https://aigora.cloud",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- NEW: Include API router ---
from app.api.v1.api import api_router #
app.include_router(api_router, prefix="/api/v1") #
# -----------------------------

@app.get("/")
async def root():
    return {"message": "Insight Pulse BFF is running!"}

@app.on_event("startup")
async def startup_event():
    print("Insight Pulse BFF starting up...")
    # Database table creation will be handled by a separate script
    pass

@app.on_event("shutdown")
async def shutdown_event():
    print("Insight Pulse BFF shutting down...")
    pass