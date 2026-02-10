from fastapi import APIRouter, Request, Response

from app.services.conversation_manager import process_message
from app.config import settings

router = APIRouter(prefix="/webhooks", tags=["WhatsApp"])


@router.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Twilio WhatsApp webhook endpoint.
    Receives incoming messages and returns TwiML responses.

    Setup (Twilio Sandbox):
    1. Go to https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
    2. Join sandbox by sending "join <sandbox-word>" to the Twilio number
    3. Set webhook URL to: https://your-domain.com/api/webhooks/whatsapp
    """
    # Parse Twilio form data
    form = await request.form()
    from_number = form.get("From", "")  # e.g. "whatsapp:+923001234567"
    body = form.get("Body", "").strip()

    if not from_number or not body:
        return Response(
            content=_twiml("Please send a message to get started."),
            media_type="text/xml",
        )

    # Process through conversation manager
    response_text = process_message(from_number, body)

    # Return TwiML response
    return Response(
        content=_twiml(response_text),
        media_type="text/xml",
    )


def _twiml(message: str) -> str:
    """Wrap message in TwiML XML format."""
    # Escape XML special characters
    escaped = (
        message
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f"<Message>{escaped}</Message>"
        "</Response>"
    )
