from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base #

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    agents = relationship("Agent", back_populates="owner")
    # Optional: Define relationships if a user has many agents (will be done in agent model)
    # agents = relationship("Agent", back_populates="owner")