"""
State management for the BRR IDP pipeline, including shared data structures and types.
"""

from typing import Any, Literal, TypedDict

class IDPGlobalState(TypedDict):
    """Global state shared across the entire pipeline."""
    raw_email_text: str
    chunks: list[str]
    redacted_text: str
    extracted_fields: dict[str, Any]
    confidence_score: float
    hitl_corrections: list[dict[str, Any]]
    final_output: dict[Literal["brr", "summary", "decision", "metadata"], Any]
    needs_review: bool