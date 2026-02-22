"""
HITL Node: pauses the graph and waits for human review/corrections.
Only runs if validator sets needs_review = True.
"""

from langgraph.types import interrupt
from state import IDPGlobalState

# === HITL Validation Logic ===

def hitl_node(state: IDPGlobalState) -> dict:
    """
    LangGraph node: pause and ask human to verify extracted fields.
    Reads:  state["extracted_fields"], state["confidence_score"]
    Writes: state["hitl_corrections"], state["extracted_fields"]
    """
    print("[ Node: hitl ]")

    extracted_fields = state.get("extracted_fields", {})
    confidence_score = state.get("confidence_score", 0.0)

    # interrupt() stops the graph here and sends the argument to the user for review.
    human_input = interrupt({
        "message": "Low confidence score. Please review and correct the extracted fields.",
        "confidence_score": confidence_score,
        "extracted_fields": extracted_fields,
        "instructions": "Return a dict with any corrected fields, or an empty dict {} to accept as-is.",
    })

    print(f"Human responded: {human_input}")

    # merge any corrections into extracted_fields
    if isinstance(human_input, dict) and human_input:
        corrected_fields = {**extracted_fields, **human_input}
        print(f"Applied {len(human_input)} correction(s)")
    else:
        corrected_fields = extracted_fields
        print("No corrections, accepted as-is")

    return {
        "extracted_fields": corrected_fields,
        "hitl_corrections": human_input if isinstance(human_input, dict) else {},
    }