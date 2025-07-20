from pydantic import BaseModel, EmailStr
from typing import List

class EmailRequest(BaseModel):
    recipient_email: EmailStr
    subject: str
    html_content: str # For the newspaper digest
    text_content: str # For the LinkedIn post

class EmailResponse(BaseModel):
    status: str
    recipient_email: EmailStr