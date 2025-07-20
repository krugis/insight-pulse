from fastapi import FastAPI, HTTPException
from . import schemas

app = FastAPI(title="Pulse Email Service")

async def send_email_mock(email_data: schemas.EmailRequest):
    """
    Mocks the action of sending an email. In a real application, this would
    connect to an SMTP server or an email API (like SendGrid, Mailgun, etc.).
    """
    print("--- 📧 MOCK EMAIL SENDER ---")
    print(f"To: {email_data.recipient_email}")
    print(f"Subject: {email_data.subject}")
    print("\n--- LinkedIn Post Content ---")
    print(email_data.text_content)
    print("\n--- HTML Digest Content (Preview) ---")
    print(email_data.html_content[:500] + "...") # Print a preview of the HTML
    print("--------------------------")
    # In a real scenario, you would handle potential sending errors here.
    return True

@app.post("/send-email", response_model=schemas.EmailResponse)
async def send_email(email_request: schemas.EmailRequest):
    """
    Receives content and an email address, and sends the daily digest.
    """
    print(f"Received request to send email to {email_request.recipient_email}")
    
    success = await send_email_mock(email_request)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email.")
        
    return schemas.EmailResponse(
        status="success",
        recipient_email=email_request.recipient_email
    )