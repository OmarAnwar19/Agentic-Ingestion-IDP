"""
Validator Node (MoE Expert 2): validates extracted fields from redacted text.
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
VALIDATOR_MODEL = os.getenv("VALIDATOR_MODEL", "llama-3.3-70b-versatile")

if LLM_PROVIDER == "ollama":
    llm = ChatOllama(
        model=VALIDATOR_MODEL,
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.3,
        num_ctx=8192,
        format="json",
    )
else:
    llm = ChatGroq(
        model=VALIDATOR_MODEL,
        temperature=0.3,
        api_key=os.getenv("GROQ_API_KEY"),
        model_kwargs={"response_format": {"type": "json_object"}},
    )

# === Prompts and templates ===

VALIDATOR_SYSTEM_PROMPT = """
You are Expert 2, the Validator. Your job is to critically review the fields extracted by Expert 1.

Be strict. Your job is to catch problems, not to approve things.

Score LOW (under 60) if:
- Any approval name, role, or sign-off is uncertain, implied, or not explicitly stated
- The go/no-go decision is unclear, unresolved, or debated
- Risks are vague, missing severity, or based on inference rather than explicit statements
- The test summary references informal language like "probably fine", "most passed", or lacks a formal result
- The extractor appears to have guessed or inferred fields not clearly written in the email

Score MEDIUM (60-79) if some fields are solid but 1-2 key fields are weak or uncertain.
Score HIGH (80+) ONLY if every field is explicitly and clearly supported by the email text.

Respond ONLY with a JSON object with this exact structure:
{
    "confidence_score": <integer 0-100>,
    "issues": [<list of strings describing specific problems found>]
}
"""

VALIDATOR_TEMPLATE = """
Here is the original redacted email content:
---
{redacted_text}
---

Here are the fields extracted by Expert 1:
---
{extracted_fields}
---

Validate the extracted fields against the original content and respond with your confidence score and issues found.
"""

# === LLM validation logic ===

def validator_node(state: IDPGlobalState) -> dict:
    """
    LangGraph node: MoE Expert 2 - validation.
    Reads:  state["redacted_text"], state["extracted_fields"]
    Writes: state["confidence_score"], state["needs_review"]
    """
    print("[ Node: validator (moe expert 2) ]")

    redacted_text = state.get("redacted_text", "")
    extracted_fields = state.get("extracted_fields", {})

    if not extracted_fields:
        print("No extracted fields to validate")
        return {"confidence_score": 0.0, "needs_review": True}

    print(f"Expert 2 (Validator) running with {VALIDATOR_MODEL}...")

    messages = [
        SystemMessage(content=VALIDATOR_SYSTEM_PROMPT),
        HumanMessage(content=VALIDATOR_TEMPLATE.format(
            redacted_text=redacted_text[:2000],
            extracted_fields=json.dumps(extracted_fields, indent=2),
        )),
    ]

    try:
        response = llm.invoke(messages)
        result = json.loads(response.content)

        confidence = float(result.get("confidence_score", 0))
        needs_review = confidence < 80
        issues = result.get("issues", [])

        print(f"Validation complete. Confidence: {confidence}%")
        if issues:
            for issue in issues:
                print(f"  - {issue}")

        return {
            "confidence_score": confidence,
            "needs_review": needs_review,
        }
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return {"confidence_score": 0.0, "needs_review": True}