from app.api.v1.endpoints import auth
from app.api.v1.endpoints import agents # Ensure this line is present and correct
from fastapi import APIRouter 

api_router = APIRouter()
api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])