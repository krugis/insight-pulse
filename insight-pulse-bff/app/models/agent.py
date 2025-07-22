from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import User # Import User model for relationship

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # ID of the agent in the external pulse-agent-manager service
    pulse_agent_manager_id = Column(String, unique=True, index=True, nullable=False)
    
    agent_name = Column(String, nullable=False, index=True)
    status = Column(String, default="active", nullable=False) # e.g., "active", "paused", "error"

    # Configuration data for the agent, stored as JSON/dict
    config_data = Column(JSON, nullable=False) # Use JSON type

    # Store API keys if using BYOK plan directly in the agent config for easy access
    apify_token = Column(String, nullable=True)
    openai_token = Column(String, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="agents")

# IMPORTANT: Add this line to app/models/user.py if you haven't already
# It defines the back-reference from User to Agent
# User.agents = relationship("Agent", back_populates="owner")