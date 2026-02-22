"""
Email Fetcher Node: reads mock email or fetches from Gmail.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.agent_toolkits import GmailToolkit

from state import IDPGlobalState

# === Environment config ===

load_dotenv()

USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "true").lower() != "false"
BRR_SUBJECT_KEYWORD = os.getenv("BRR_EMAIL_SUBJECT_KEYWORD", "BRR")

MOCK_EMAIL_FILE_NAME = os.getenv("MOCK_EMAIL_FILE_NAME", "brr_email_001.txt")
MOCK_EMAIL_PATH = Path(__file__).parent.parent / "data" / "mock_emails" / MOCK_EMAIL_FILE_NAME

# === Helper functions ===
def load_mock_email() -> str:
    """Load mock email text from disk."""
    if not MOCK_EMAIL_PATH.exists():
        raise FileNotFoundError(f"Mock email not found at: {MOCK_EMAIL_PATH}")
    with open(MOCK_EMAIL_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    print(f"Loaded mock email from {MOCK_EMAIL_PATH}")
    return content

# === Fetch email function ===

def email_fetcher_node(state: IDPGlobalState) -> dict:
    """
    LangGraph node: fetches a BRR email and writes raw text to state.
    Returns: only the new state dict for this node (not the full state).
    """
    print("[ Node: email_fetcher ]")

    if USE_MOCK_DATA:
        raw_text = load_mock_email()
        return {"raw_email_text": raw_text}

    toolkit = GmailToolkit()
    tools = toolkit.get_tools()

    search_tool = next((t for t in tools if "search" in t.name.lower()), None)
    if not search_tool:
        raise RuntimeError("Gmail search tool not found in toolkit")

    result = search_tool.run(f"subject:{BRR_SUBJECT_KEYWORD}")
    return {"raw_email_text": result}