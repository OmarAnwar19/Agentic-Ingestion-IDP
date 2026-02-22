"""
PII Redactor Node: removes PII from chunks in state.
Two-pass: regex first, then optional Presidio upgrade later.
"""

import re
from state import IDPGlobalState

# === PII Redaction logic ===

def _regex_redact(text: str) -> str:
    """Apply regex patterns to catch common PII."""
    text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "<EMAIL>", text)
    text = re.sub(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", "<PHONE>", text)
    text = re.sub(r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b", "<SSN>", text)
    text = re.sub(r"\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b", "<CREDIT_CARD>", text)
    text = re.sub(r"\b[A-Z]{3}-\d{4}\b", "<PROJECT_CODE>", text)
    return text

def _presidio_redact(text: str) -> str:
    # TODO: replace with real Presidio logic later
    return text

def pii_redactor_node(state: dict) -> dict:
    """
    LangGraph node: redact PII from all chunked text.
    Reads:  state["chunks"]
    Writes: state["redacted_text"]
    """
    print("[ Node: pii_redactor ]")

    chunks = state.get("chunks", [])
    if not chunks:
        print("No chunks to redact")
        return {"redacted_text": ""}

    full_text = "\n".join(chunks)
    print(f"Redacting {len(chunks)} chunks ({len(full_text)} chars)...")

    # First pass: regex-based redaction
    redacted_text = _regex_redact(full_text)
    # Second pass: Presidio (if available)
    final_redacted = _presidio_redact(redacted_text)

    # print the redacted fields for debugging
    redacted_fields = []
    for pattern in [
        r"<EMAIL>",
        r"<PHONE>",
        r"<SSN>",
        r"<CREDIT_CARD>",
        r"<PROJECT_CODE>",
    ]:
        matches = re.findall(pattern, final_redacted)
        if matches:
            redacted_fields.append((pattern, len(matches)))
    print(f"Redacted fields: {redacted_fields}")

    print("Redaction complete")
    return {"redacted_text": final_redacted}