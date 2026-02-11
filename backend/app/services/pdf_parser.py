"""PDF bank statement parser using Claude Files API extraction."""

import json
import re
from io import BytesIO
from typing import Any, Dict, List

import anthropic
import pdfplumber

from app.config import settings

CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
CLAUDE_MAX_TOKENS = 16000
CLAUDE_API_TIMEOUT_SECONDS = 85.0
FILES_API_BETA = "files-api-2025-04-14"
PDF_MIME_TYPE = "application/pdf"
MIN_VALID_TRANSACTIONS = 2

TRANSACTION_EXTRACTION_PROMPT = """You are a bank statement parser. Look at this PDF bank statement and extract ALL transactions.

For each transaction, extract:
- date: The transaction date in YYYY-MM-DD format
- name: The merchant/payee/description
- amount: The amount as a number (positive = expense/debit, negative = income/credit/deposit)

IMPORTANT RULES:
- Extract EVERY transaction you can find, don't skip any
- Convert all dates to YYYY-MM-DD format
- For amounts: expenses/debits/withdrawals should be POSITIVE, income/credits/deposits should be NEGATIVE
- If a transaction has both debit and credit columns, use whichever is non-zero
- Clean up merchant names (remove extra spaces, transaction codes, etc.)
- If the currency is not USD, still extract the numeric amount (the system handles currency separately)
- Skip summary rows, balance rows, header rows - only extract actual transactions

Return ONLY a valid JSON array, no other text. Example:
[
  {"date": "2024-01-15", "name": "Starbucks Coffee", "amount": 5.50},
  {"date": "2024-01-14", "name": "Direct Deposit - Payroll", "amount": -3500.00}
]"""


class PDFParseError(Exception):
    """Raised when PDF parsing fails due to invalid file or malformed output."""


class PDFServiceUnavailableError(Exception):
    """Raised when Anthropic Files or Messages APIs fail."""


def _extract_anthropic_error_detail(exc: anthropic.APIStatusError) -> str:
    """Extract the most useful Anthropic error detail for debugging."""
    message = ""
    error_type = ""

    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        error_obj = body.get("error")
        if isinstance(error_obj, dict):
            message = str(error_obj.get("message", "")).strip()
            error_type = str(error_obj.get("type", "")).strip()

    if not message:
        response = getattr(exc, "response", None)
        if response is not None:
            try:
                response_json = response.json()
                if isinstance(response_json, dict):
                    error_obj = response_json.get("error")
                    if isinstance(error_obj, dict):
                        message = str(error_obj.get("message", "")).strip()
                        error_type = str(error_obj.get("type", "")).strip()
            except Exception:
                pass

    if not message:
        message = str(exc).strip() or "Unknown Anthropic API error"

    request_id = getattr(exc, "request_id", None)
    if request_id:
        if error_type:
            return f"{error_type}: {message} (request_id: {request_id})"
        return f"{message} (request_id: {request_id})"

    if error_type:
        return f"{error_type}: {message}"
    return message


def _build_client() -> anthropic.Anthropic:
    """Build and validate Anthropic client."""
    if not settings.anthropic_api_key:
        raise PDFServiceUnavailableError("Anthropic API key is not configured.")
    # Disable automatic retries so failed requests are not silently repeated.
    return anthropic.Anthropic(
        api_key=settings.anthropic_api_key,
        timeout=CLAUDE_API_TIMEOUT_SECONDS,
        max_retries=0,
    )


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes for preview endpoint."""
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            pages_text: List[str] = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
    except Exception as exc:
        raise PDFParseError(f"Failed to read PDF: {exc}") from exc

    if not pages_text:
        raise PDFParseError("No text could be extracted from the PDF.")
    return "\n".join(pages_text)


def get_pdf_preview(pdf_bytes: bytes) -> Dict:
    """Get a preview of the PDF content for UI display."""
    full_text = _extract_pdf_text(pdf_bytes)
    lines = [line.strip() for line in full_text.split("\n") if line.strip()]
    return {
        "total_lines": len(lines),
        "preview_text": "\n".join(lines[:30]),
        "full_text_length": len(full_text),
    }


def _upload_pdf_file(client: anthropic.Anthropic, pdf_bytes: bytes) -> str:
    """Upload PDF bytes to Claude Files API and return file_id."""
    try:
        uploaded_file = client.beta.files.upload(
            file=("bank_statement.pdf", BytesIO(pdf_bytes), PDF_MIME_TYPE),
        )
        return uploaded_file.id
    except anthropic.APITimeoutError as exc:
        raise PDFServiceUnavailableError(
            "Claude Files API timed out before upload completed. Please retry once."
        ) from exc
    except anthropic.APIConnectionError as exc:
        raise PDFServiceUnavailableError(
            "Could not reach Claude Files API. Please try again."
        ) from exc
    except anthropic.APIStatusError as exc:
        detail = _extract_anthropic_error_detail(exc)
        if exc.status_code == 400:
            raise PDFParseError(
                f"Claude rejected the uploaded PDF: {detail}"
            ) from exc
        raise PDFServiceUnavailableError(
            f"Claude Files API request failed ({exc.status_code}): {detail}"
        ) from exc
    except anthropic.APIError as exc:
        raise PDFServiceUnavailableError(
            "Unexpected Claude Files API error. Please try again."
        ) from exc


def _delete_uploaded_file(client: anthropic.Anthropic, file_id: str) -> None:
    """Best-effort cleanup of uploaded Claude file."""
    try:
        client.beta.files.delete(file_id=file_id, betas=[FILES_API_BETA])
    except Exception:
        # Cleanup failures should not block user flow.
        pass


def _request_transaction_extraction(client: anthropic.Anthropic, file_id: str) -> Any:
    """Request transaction extraction from uploaded PDF file."""
    try:
        return client.beta.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            betas=[FILES_API_BETA],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": TRANSACTION_EXTRACTION_PROMPT,
                        },
                        {
                            "type": "document",
                            "source": {
                                "type": "file",
                                "file_id": file_id,
                            },
                        },
                    ],
                }
            ],
        )
    except anthropic.APITimeoutError as exc:
        raise PDFServiceUnavailableError(
            "Claude extraction timed out before completion. Please retry once."
        ) from exc
    except anthropic.APIConnectionError as exc:
        raise PDFServiceUnavailableError(
            "Could not reach Claude Messages API. Please try again."
        ) from exc
    except anthropic.APIStatusError as exc:
        detail = _extract_anthropic_error_detail(exc)
        if exc.status_code == 400:
            raise PDFParseError(
                f"Claude rejected the extraction request: {detail}"
            ) from exc
        raise PDFServiceUnavailableError(
            f"Claude Messages API request failed ({exc.status_code}): {detail}"
        ) from exc
    except anthropic.APIError as exc:
        raise PDFServiceUnavailableError(
            "Unexpected Claude Messages API error. Please try again."
        ) from exc


def _extract_text_from_message(message: Any) -> str:
    """Extract concatenated text blocks from Claude message response."""
    content = getattr(message, "content", None)
    if not content:
        raise PDFParseError("Claude returned an empty response.")

    text_blocks: List[str] = []
    for block in content:
        block_type = getattr(block, "type", None)
        block_text = getattr(block, "text", None)
        if block_type == "text" and block_text:
            text_blocks.append(block_text)

    if not text_blocks:
        raise PDFParseError("Claude response did not contain transaction text output.")
    return "\n".join(text_blocks)


def _extract_json_from_response(text: str) -> list:
    """Robustly extract a JSON array from Claude's response."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        result = json.loads(cleaned)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start >= 0 and end > start:
        try:
            result = json.loads(cleaned[start : end + 1])
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    raise PDFParseError(
        "Could not extract transactions from the AI response. "
        "Please try a different PDF or use CSV upload instead."
    )


def _normalize_transactions(transactions: List[Any]) -> List[Dict]:
    """Normalize and validate extracted transaction rows."""
    normalized: List[Dict] = []
    for txn in transactions:
        if not isinstance(txn, dict):
            continue

        date = txn.get("date", "")
        name = txn.get("name", "Unknown")
        amount = txn.get("amount")
        if not date or amount is None:
            continue

        try:
            parsed_amount = float(amount)
        except (ValueError, TypeError):
            continue

        normalized.append(
            {
                "date": str(date),
                "name": str(name),
                "amount": parsed_amount,
            }
        )
    return normalized


async def parse_pdf_with_claude(pdf_bytes: bytes) -> List[Dict]:
    """Extract transactions from PDF using Claude Files API."""
    client = _build_client()
    file_id = _upload_pdf_file(client, pdf_bytes)

    try:
        message = _request_transaction_extraction(client, file_id=file_id)
    finally:
        _delete_uploaded_file(client, file_id=file_id)

    response_text = _extract_text_from_message(message)
    transactions = _extract_json_from_response(response_text)

    if len(transactions) == 0:
        raise PDFParseError("No transactions found in the PDF.")

    valid_transactions = _normalize_transactions(transactions)
    if len(valid_transactions) < MIN_VALID_TRANSACTIONS:
        raise PDFParseError(
            f"Only {len(valid_transactions)} valid transactions found. "
            "The PDF may not contain a proper bank statement."
        )

    return valid_transactions
