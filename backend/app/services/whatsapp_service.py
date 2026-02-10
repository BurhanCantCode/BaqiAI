"""Twilio WhatsApp messaging service."""

from twilio.rest import Client

from app.config import settings


def get_twilio_client() -> Client:
    """Create Twilio client from settings."""
    return Client(settings.twilio_account_sid, settings.twilio_auth_token)


def send_whatsapp_message(to: str, body: str) -> str:
    """
    Send a WhatsApp message via Twilio sandbox.

    Args:
        to: Recipient phone number in format 'whatsapp:+923001234567'
        body: Message text

    Returns:
        Message SID
    """
    client = get_twilio_client()
    message = client.messages.create(
        from_=f"whatsapp:{settings.twilio_whatsapp_number}",
        to=to,
        body=body,
    )
    return message.sid
