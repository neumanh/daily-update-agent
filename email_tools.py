import os
import smtplib
from email.mime.text import MIMEText
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "hadas.doron@gmail.com"


def _get_env_variable(name: str) -> str:
    """
    Retrieve an environment variable and fail fast if missing.

    Args:
        name (str): Environment variable name

    Returns:
        str: Value of the environment variable

    Raises:
        ValueError: If the variable is not set
    """
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def send_email(address: str, subject: str, body: str) -> None:
    """
    Send an email using Gmail SMTP.

    This function:
    - Builds a plain-text email
    - Connects securely using TLS
    - Authenticates using credentials from environment variables

    Required environment variables:
        SMTP_PASSWORD

    Args:
        address (str): Recipient email address
        subject (str): Email subject
        body (str): Email body (plain text)

    Raises:
        ValueError: If required environment variables are missing
        smtplib.SMTPException: If sending fails
    """
    smtp_password = _get_env_variable("SMTP_PASSWORD")

    # Build email message
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = address

    # Connect to SMTP server and send email
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()  # Upgrade to secure connection
        server.login(SENDER_EMAIL, smtp_password)
        server.send_message(msg)


def send_error_update(error_message: str) -> None:
    """
    Send an error notification email to the default user.

    Args:
        error_message (str): Error details to include in the email
    """
    subject = "עדכון שגיאה מהסוכן המגניב"
    recipient = _get_env_variable("MY_EMAIL")

    send_email(
        address=recipient,
        subject=subject,
        body=error_message
    )


def _send_update_email(env_key: str, subject: str, body: str) -> None:
    """
    Generic helper for sending update emails to predefined recipients.

    Args:
        env_key (str): Environment variable containing recipient email
        subject (str): Email subject
        body (str): Email body
    """
    recipient = _get_env_variable(env_key)
    send_email(address=recipient, subject=subject, body=body)


def send_update_email_to_myself(subject: str, body: str) -> None:
    """Send an update email to MY_EMAIL."""
    _send_update_email("MY_EMAIL", subject, body)


def send_update_email_to_hallel(subject: str, body: str) -> None:
    """Send an update email to HALLELS_EMAIL."""
    _send_update_email("HALLELS_EMAIL", subject, body)


def send_update_email_to_michael(subject: str, body: str) -> None:
    """Send an update email to MICHAELS_EMAIL."""
    _send_update_email("MICHAELS_EMAIL", subject, body)


def send_update_email_to_israel(subject: str, body: str) -> None:
    """Send an update email to ISRAELS_EMAIL."""
    _send_update_email("ISRAELS_EMAIL", subject, body)


def send_update_email_to_yehonatan(subject: str, body: str) -> None:
    """Send an update email to YEHONATANS_EMAIL."""
    _send_update_email("YEHONATANS_EMAIL", subject, body)