from sqlalchemy import Column, Integer, String, Date, JSON
from app.db.database import Base

class DailyDigest(Base):
    __tablename__ = "daily_digests"

    id = Column(Integer, primary_key=True, index=True)
    publication_date = Column(Date, unique=True, index=True)
    content_json = Column(JSON)