import smtplib
import os
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com") # Default to Gmail if not set
SMTP_PORT = int(os.getenv("SMTP_PORT", 465)) # Default to 465 if not set

def send_email_alert(to_email, subject, body):
    """Sends an email alert with specific error handling."""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("❌ Email credentials not set in .env file. Cannot send email.")
        return

    msg = EmailMessage()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"📩 Alert sent to {to_email}")
    except smtplib.SMTPAuthenticationError:
        print(f"❌ Authentication failed for {EMAIL_ADDRESS}. Check your email/password or app password.")
    except ConnectionRefusedError:
        print(f"❌ Connection refused by the server {SMTP_SERVER}. Check server/port settings.")
    except Exception as e:
        print(f"❌ An unexpected error occurred while sending email to {to_email}: {e}")

