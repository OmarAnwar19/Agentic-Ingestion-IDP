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

MOCK_DATA_DIR = Path(__file__).parent.parent / "data" / "mock_emails"
DEFAULT_MOCK_FILE = os.getenv("MOCK_EMAIL_FILE_NAME", "brr_email_001.txt")


# === Helper functions ===

def load_mock_email(filename: str) -> str:
    """Load mock email text from disk."""
    path = MOCK_DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Mock email not found at: {path}")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    print(f"Loaded mock email: {filename}")
    return content

# === Fetch email function ===

def email_fetcher_node(state: IDPGlobalState) -> dict:
    """
    LangGraph node: fetches a BRR email and writes raw text to state.
    Returns: only the new state dict for this node (not the full state).
    """
    print("[ Node: email_fetcher ]")

    if USE_MOCK_DATA:
        filename = state.get("mock_email_file") or DEFAULT_MOCK_FILE
        raw_text = load_mock_email(filename)
        return {"raw_email_text": raw_text}

    toolkit = GmailToolkit()
    tools = toolkit.get_tools()

    search_tool = next((t for t in tools if "search" in t.name.lower()), None)
    if not search_tool:
        raise RuntimeError("Gmail search tool not found in toolkit")

    result = search_tool.run(f"subject:{BRR_SUBJECT_KEYWORD}")
    return {"raw_email_text": result}