from fastapi import APIRouter

from app.api.v1.endpoints import auth #

api_router = APIRouter()
api_router.include_router(auth.router, tags=["Authentication"]) #

# Add other routers here as they are implemented, e.g.:
# from app.api.v1.endpoints import users
# api_router.include_router(users.router, prefix="/users", tags=["Users"])
# from app.api.v1.endpoints import agents
# api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])