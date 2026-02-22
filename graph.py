"""
Graph definition for the BRR IDP pipeline.
Wires all nodes together and defines routing logic.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from state import IDPGlobalState

from nodes.email_fetcher import email_fetcher_node
from nodes.chunker import semantic_chunker_node
from nodes.pii_redactor import pii_redactor_node
from nodes.extractor import extractor_node
from nodes.validator import validator_node
from nodes.hitl import hitl_node
from nodes.output import output_builder_node

# === Routing logic ===

def route_after_validator(state: IDPGlobalState) -> str:
    """
    Conditional edge: decide where to go after validation.
    If needs_review is True, go to hitl
    If needs_review is False, go straight to output_builder
    """
    if state.get("needs_review", False):
        print("Routing to HITL (low confidence)")
        return "hitl"
    print("Routing to output (confidence OK)")
    return "output_builder"


# === Build the graph ===

def build_graph():
    """Construct and compile the BRR pipeline graph."""

    memory = MemorySaver()

    builder = StateGraph(IDPGlobalState)

    # Add nodes
    builder.add_node("email_fetcher", email_fetcher_node)
    builder.add_node("chunker", semantic_chunker_node)
    builder.add_node("pii_redactor", pii_redactor_node)
    builder.add_node("extractor", extractor_node)
    builder.add_node("validator", validator_node)
    builder.add_node("hitl", hitl_node)
    builder.add_node("output_builder", output_builder_node)

    # Define edges
    builder.add_edge(START, "email_fetcher")
    builder.add_edge("email_fetcher", "chunker")
    builder.add_edge("chunker", "pii_redactor")
    builder.add_edge("pii_redactor", "extractor")
    builder.add_edge("extractor", "validator")

    # Conditional edges
    builder.add_conditional_edges(
        "validator",
        route_after_validator,
        {
            "hitl": "hitl",
            "output_builder": "output_builder",
        }
    )

    # Route to end and compile with memory
    builder.add_edge("hitl", "output_builder")
    builder.add_edge("output_builder", END)
    return builder.compile(checkpointer=memory)

graph = build_graph()