"""
Extractor Node (MoE Expert 1): extracts structured fields from redacted text.
"""

import json
import os
from dotenv import load_dotenv
from state import IDPGlobalState
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# === Environment config and model setup ===

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
EXTRACTOR_MODEL = os.getenv("EXTRACTOR_MODEL", "llama-3.3-70b-versatile")

if LLM_PROVIDER == "ollama":
    llm = ChatOllama(
        model=EXTRACTOR_MODEL,
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.1,
        num_ctx=8192,
        format="json",
    )
else:
    llm = ChatGroq(
        model=EXTRACTOR_MODEL,
        temperature=0.1,
        api_key=os.getenv("GROQ_API_KEY"),
        model_kwargs={"response_format": {"type": "json_object"}},
    )

# === Prompts and templates ===

EXTRACTOR_SYSTEM_PROMPT = """
You are Expert 1, the Extractor. Your job is to read the redacted email content and extract key information relevant to a Business Risk Review (BRR).
Focus on identifying:
- Approvals: who approved, their role, and any conditions
- Risks: what are the risks mentioned, their severity, and mitigation plans
- Go/No-Go decision: is the recommendation to proceed, hold, or stop?

Extract this information into a structured JSON format with the following fields:
- approvals: list of {name, role, conditions}
- risks: list of {description, severity, mitigation}
- go_no_go_status: PROCEED/HOLD/STOP
- test_summary: brief summary of any testing results mentioned
"""

EXTRACTOR_TEMPLATE = """
Extract the relevant fields from this redacted email content:

---
{redacted_text}
---

Remember:
- Use the exact JSON structure specified in the system prompt.
- For any missing information, use null or empty lists as appropriate.
- Do not guess or infer anything not explicitly stated.
"""

_EMPTY_RESULT = {
    "approvals": [],
    "risks": [],
    "go_no_go_status": "HOLD",
    "test_summary": None,
}

# === LLM extraction logic ===

def extractor_node(state: IDPGlobalState) -> dict:
    """
    LangGraph node: MoE Expert 1 - extraction.
    Reads:  state["redacted_text"]
    Writes: state["extracted_fields"]
    """
    print("[ Node: extractor (moe expert 1) ]")

    redacted_text = state.get("redacted_text", "")

    if not redacted_text.strip():
        print("No redacted text to extract from")
        return {"extracted_fields": _EMPTY_RESULT}

    print(f"Expert 1 (Extractor) running with {EXTRACTOR_MODEL}...")

    messages = [
        SystemMessage(content=EXTRACTOR_SYSTEM_PROMPT),
        HumanMessage(content=EXTRACTOR_TEMPLATE.format(redacted_text=redacted_text[:3000])),
    ]

    try:
        response = llm.invoke(messages)
        extracted = json.loads(response.content)
        print("Extraction complete")
        return {"extracted_fields": extracted}
    except Exception as e:
        print(f"Extraction failed: {e}")
        return {"extracted_fields": _EMPTY_RESULT}