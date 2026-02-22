"""
Chunker node for BRR IDP LangGraph.
Reads raw email text from state, splits into semantic chunks, writes back to state.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from state import IDPGlobalState

# === Chunking config ===

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
BRR_SEPARATORS = [
    "\n\n",
    "\n",
    r"\n-{3,}\n",
    r"\n={3,}\n",
    ": ",
]

# === Chunking logic ===

def _detect_section(chunk: str) -> str:
    """Naive section detector based on BRR keywords."""
    chunk_lower = chunk.lower()
    if "readiness" in chunk_lower: return "readiness"
    if "risk" in chunk_lower: return "risk"
    if "approval" in chunk_lower: return "approval"
    if "build" in chunk_lower: return "build"
    return "general"


def semantic_chunker_node(state: IDPGlobalState) -> dict:
    """
    LangGraph node: split document into semantic chunks.
    Reads:  state["raw_email_text"]
    Writes: state["chunks"]
    """
    print("[ Node: chunker ]")

    source_text = state.get("raw_email_text", "")

    if not source_text.strip():
        print("No text to chunk")
        return {"chunks": []}

    print(f"Chunking {len(source_text)} chars...")

    splitter = RecursiveCharacterTextSplitter(
        separators=BRR_SEPARATORS,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=True,
        keep_separator=True,
    )
    raw_chunks = splitter.split_text(source_text)

    chunks = []
    for i, chunk in enumerate(raw_chunks):
        section = _detect_section(chunk)
        chunks.append(chunk)
        print(f"  Chunk {i+1}: [{section}] {len(chunk)} chars")

    return {"chunks": chunks}