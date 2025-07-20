from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    plan_type = Column(String, default="subscribe")
    
    # Store encrypted keys if the user provides them
    encrypted_apify_token = Column(String, nullable=True)
    encrypted_openai_token = Column(String, nullable=True)
    
    # Store preferences as a JSON object
    preferences = Column(JSON)
    
    profiles = relationship("Profile", back_populates="agent")

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    
    agent = relationship("Agent", back_populates="profiles")