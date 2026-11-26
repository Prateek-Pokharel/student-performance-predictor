import smtplib
import secrets
import sys
import os
from email.message import EmailMessage

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SENDER_EMAIL, SENDER_PASSWORD, SMTP_SERVER, SMTP_PORT

# Generates secure 6-digit OTP
# Called By: ui/auth/login_ui.py -> VerifyIdentityWidget
# Returns: int (e.g., 123456)
def generate_otp() -> int:
    return secrets.randbelow(900000) + 100000

# Sends OTP via SMTP (Gmail)
# Called By: ui/auth/login_ui.py -> EmailSenderWorker
# Returns: Bool (True if sent)
def send_otp_email(subject: str, body: str, to_email: str) -> bool:
    msg = EmailMessage()
    msg.set_content(body)
    msg['subject'] = subject
    msg['to'] = to_email
    msg['from'] = SENDER_EMAIL

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email Service Error: {e}")
        return False