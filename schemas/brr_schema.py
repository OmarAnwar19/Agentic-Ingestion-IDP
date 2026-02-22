"""
Pydantic schema for a Build Readiness Review (BRR) document.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field

class Approval(BaseModel):
    name: str
    role: str
    conditions: Optional[str] = None

class Risk(BaseModel):
    description: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    mitigation: Optional[str] = None

class BRRSchema(BaseModel):
    """Structured representation of a Build Readiness Review."""
    approvals: list[Approval] = Field(default_factory=list)
    risks: list[Risk] = Field(default_factory=list)
    go_no_go_status: Literal["PROCEED", "HOLD", "STOP"] = "HOLD"
    test_summary: Optional[str] = None