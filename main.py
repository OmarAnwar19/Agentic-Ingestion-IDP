"""
Streamlit UI for the BRR IDP pipeline.
Run with: streamlit run main.py
"""

from datetime import datetime
import json
import os
import streamlit as st
from dotenv import load_dotenv

from langgraph.types import Command
from langfuse.langchain import CallbackHandler

from graph import graph

# === Page config ===

load_dotenv()

for key, value in st.secrets.items():
    os.environ.setdefault(key, str(value))
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "true").lower() != "false"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
EXTRACTOR_MODEL = os.getenv("EXTRACTOR_MODEL", "llama-3.3-70b-versatile")
VALIDATOR_MODEL = os.getenv("VALIDATOR_MODEL", "llama-3.3-70b-versatile")

    
st.set_page_config(
    page_title="Agentic Ingestion Pipeline Demo",
    layout="wide",
)

st.title("Agentic Ingestion Pipeline")
st.info("Demo of a human-in-the-loop document processing pipeline built with LangGraph. Extracts structured fields from emails, validates confidence, and routes low-confidence results for human review before generating a final report. Select a mock email from the sidebar to test both the clean and HITL paths.")

# === Session state ===

if "thread_id" not in st.session_state:
    st.session_state.thread_id = "brr-session-1"

if "pipeline_result" not in st.session_state:
    st.session_state.pipeline_result = None

if "stage" not in st.session_state:
    st.session_state.stage = "idle"  # idle | running | hitl | done

if "graph_output" not in st.session_state:
    st.session_state.graph_output = None

if "mock_email_file" not in st.session_state:
    st.session_state.mock_email_file = "brr_email_001.txt"

# === Sidebar ===

with st.sidebar:
    st.header("Config")
    st.divider()
    st.markdown("**Mock Email**")
    mock_file = st.selectbox(
        "mock_file",
        options=["brr_email_001.txt", "brr_email_002.txt"],
        format_func=lambda x: "Email 1 - clean (no HITL)" if x == "brr_email_001.txt" else "Email 2 - vague (triggers HITL)",
        label_visibility="collapsed",
    )
    st.session_state.mock_email_file = mock_file
    thread_id = st.text_input("Thread ID", value=st.session_state.thread_id)
    st.session_state.thread_id = thread_id
    st.divider()
    st.markdown("**Models**")
    st.code(f"Extractor: {EXTRACTOR_MODEL}\nValidator: {VALIDATOR_MODEL}\nProvider:  {LLM_PROVIDER}", language="text")
    st.divider()
    st.markdown("**Pipeline**")
    st.markdown("""
        1. Email Fetcher
        2. Chunker
        3. PII Redactor
        4. Extractor
        5. Validator
        6. HITL *(if needed)*
        7. Output Builder
    """)

# === Helpers ===

def get_config() -> dict:
    """Return the LangGraph config dict for the current thread."""
    langfuse_handler = CallbackHandler()
    return {
        "configurable": {"thread_id": st.session_state.thread_id},
        "callbacks": [langfuse_handler],
    }

def get_initial_state() -> dict:
    """Return a blank pipeline state."""
    return {
        "raw_email_text": "",
        "chunks": [],
        "redacted_text": "",
        "extracted_fields": {},
        "confidence_score": 0.0,
        "hitl_corrections": {},
        "final_output": {},
        "needs_review": False,
        "mock_email_file": st.session_state.get("mock_email_file", "brr_email_001.txt"),
    }

# === Stage: idle ===

if st.session_state.stage == "idle":
    if USE_MOCK_DATA:
        st.warning("Using MOCK DATA - no real emails will be fetched.")

    if st.button("Run Pipeline", type="primary", use_container_width=True):
        st.session_state.stage = "running"
        st.rerun()

# === Stage: running ===

elif st.session_state.stage == "running":
    st.subheader("Running pipeline...")

    try:
        with st.spinner("Processing..."):
            result = graph.invoke(get_initial_state(), config=get_config())

        # interrupt() was triggered, pause for human review
        if "__interrupt__" in result:
            st.session_state.pipeline_result = result
            st.session_state.stage = "hitl"
        else:
            st.session_state.graph_output = result
            st.session_state.stage = "done"

        st.rerun()

    except Exception as e:
        st.error(f"Pipeline failed: {e}")
        st.session_state.stage = "idle"

# === Stage: hitl ===

elif st.session_state.stage == "hitl":
    st.subheader("Human Review Required")

    result = st.session_state.pipeline_result
    interrupt_payload = result["__interrupt__"][0].value

    confidence = interrupt_payload.get("confidence_score", 0)
    extracted = interrupt_payload.get("extracted_fields", {})

    st.warning(f"Confidence score: {confidence:.0f}% is low. Please review the extracted fields below before continuing.")
    st.divider()

    with st.form("hitl_form"):
        st.markdown("### Extracted Fields")
        st.caption("Edit any incorrect values, then click Confirm.")

        col1, col2 = st.columns(2)

        with col1:
            go_no_go = st.selectbox(
                "Go/No-Go Status",
                options=["PROCEED", "HOLD", "STOP"],
                index=["PROCEED", "HOLD", "STOP"].index(
                    extracted.get("go_no_go_status") or "HOLD"
                ),
            )
            test_summary = st.text_area(
                "Test Summary",
                value=extracted.get("test_summary") or "",
                height=100,
            )

        with col2:
            st.markdown("**Approvals** *(JSON)*")
            approvals_raw = st.text_area(
                "approvals_json",
                value=json.dumps(extracted.get("approvals", []), indent=2),
                height=150,
                label_visibility="collapsed",
            )
            st.markdown("**Risks** *(JSON)*")
            risks_raw = st.text_area(
                "risks_json",
                value=json.dumps(extracted.get("risks", []), indent=2),
                height=150,
                label_visibility="collapsed",
            )

        submitted = st.form_submit_button("Confirm and Continue", type="primary")

    if submitted:
        try:
            approvals = json.loads(approvals_raw)
            risks = json.loads(risks_raw)
        except json.JSONDecodeError:
            st.error("Invalid JSON in approvals or risks - please fix and resubmit.")
            st.stop()

        corrections = {
            "go_no_go_status": go_no_go,
            "test_summary": test_summary,
            "approvals": approvals,
            "risks": risks,
        }

        try:
            with st.spinner("Resuming pipeline..."):
                final_result = graph.invoke(
                    Command(resume=corrections),
                    config=get_config(),
                )
            st.session_state.graph_output = final_result
            st.session_state.stage = "done"
            st.rerun()
        except Exception as e:
            st.error(f"Pipeline failed on resume: {e}")
            st.stop()

# === Stage: done ===

elif st.session_state.stage == "done":
    st.success("Pipeline complete.")

    output = st.session_state.graph_output.get("final_output", {})
    brr_text = output.get("brr", "")
    pdf_path = output.get("pdf_path", "")
    confidence = output.get("confidence_score", 0)
    corrected = output.get("human_corrected", False)

    col1, col2, col3 = st.columns(3)
    col1.metric("Confidence Score", f"{confidence:.0f}%")
    col2.metric("Human Corrected", "Yes" if corrected else "No")
    col3.metric("Generated At", output.get("generated_at", "")[:10])

    st.divider()

    st.markdown("### Cleaned BRR")
    if brr_text:
        st.code(brr_text, language="text")
    else:
        st.warning("Output text is empty. Check the debug state below to diagnose.")
        st.json(st.session_state.graph_output)

    if pdf_path:
        try:
            with open(pdf_path, "rb") as f:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    label="Download BRR as PDF",
                    data=f,
                    file_name=f"BRR_{timestamp}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary",
                )
        except FileNotFoundError:
            st.warning(f"PDF not found at: {pdf_path}")

    st.divider()

    with st.expander("Full pipeline state (debug)"):
        st.json(st.session_state.graph_output)

    if st.button("Run Again", use_container_width=True):
        st.session_state.stage = "idle"
        st.session_state.pipeline_result = None
        st.session_state.graph_output = None
        st.rerun()
