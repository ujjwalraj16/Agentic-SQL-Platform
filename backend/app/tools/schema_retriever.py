"""
tools/schema_retriever.py – Schema retrieval tool used by the Planner Agent.

Bridges the Planner with the FAISS vector store to retrieve only the
relevant tables for the current question, reducing LLM token usage.
"""

from __future__ import annotations
from typing import Any
from app.retrieval.vector_store import get_vector_store
from app.database.schema import schema_to_compact_text


def retrieve_relevant_schema(
    question: str,
    full_schema: dict[str, Any],
    k: int = 6,
) -> tuple[list[str], str, float]:
    """
    Retrieve relevant tables for a question using FAISS.

    Returns:
        (relevant_tables, schema_text, retrieval_time_ms)
    """
    vs = get_vector_store()
    tables, retrieval_ms = vs.retrieve_relevant_tables(question, k=k)
    schema_text = schema_to_compact_text(full_schema, tables)
    return tables, schema_text, retrieval_ms
