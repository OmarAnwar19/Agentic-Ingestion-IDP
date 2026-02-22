"""
Output Builder Node: assembles the final cleaned BRR and exports to PDF.
"""

from datetime import datetime
from pathlib import Path

from state import IDPGlobalState

from utils.output_brr_pdf import format_brr, export_pdf

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "output"

# === Output Builder Node ===

def output_builder_node(state: IDPGlobalState) -> dict:
    """
    LangGraph node: assemble and export final BRR as PDF.
    Reads:  state["extracted_fields"], state["confidence_score"], state["hitl_corrections"]
    Writes: state["final_output"]
    """
    print("[ Node: output_builder ]")

    extracted_fields = state.get("extracted_fields", {})
    confidence_score = state.get("confidence_score", 0.0)
    hitl_corrections = state.get("hitl_corrections", {})

    brr_text = format_brr(extracted_fields, confidence_score, hitl_corrections)

    # --- Export to PDF ---
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = OUTPUT_DIR / f"BRR_{timestamp}.pdf"

    export_pdf(brr_text, pdf_path)
    print(f"PDF saved to: {pdf_path}")

    print("\n" + brr_text)

    return {
        "final_output": {
            "brr": brr_text,
            "pdf_path": str(pdf_path),
            "confidence_score": confidence_score,
            "human_corrected": bool(hitl_corrections),
            "generated_at": datetime.now().isoformat(),
        }
    }