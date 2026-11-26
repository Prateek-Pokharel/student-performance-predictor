import os

# Set these environment variables for your own Oracle and SMTP accounts.
# Never commit real passwords or email app passwords to source control.
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_SERVICE = os.getenv("DB_SERVICE", "XE")
DB_USER_ADMIN = os.getenv("DB_USER_ADMIN", "PROJECT_ADMIN")
DB_PASSWORD_DEFAULT = os.getenv("DB_PASSWORD_DEFAULT", "")

SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
