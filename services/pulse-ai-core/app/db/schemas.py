from pydantic import BaseModel
from datetime import date

class DigestResponse(BaseModel):
    id: int
    publication_date: date

    class Config:
        from_attributes = True