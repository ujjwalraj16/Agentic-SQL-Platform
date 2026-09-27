"""
graph/state.py – LangGraph state definition for the agentic SQL workflow.

The AgentState holds all data that flows between nodes in the graph.
Using TypedDict for LangGraph compatibility.
"""

from __future__ import annotations
from typing import Any, Optional, TypedDict


class AgentState(TypedDict, total=False):
    # ── Input ────────────────────────────────────────────────────────────────
    question: str
    session_id: str
    query_id: str

    # ── Schema context ────────────────────────────────────────────────────────
    schema: dict[str, Any]                 # Full extracted schema
    relevant_tables: list[str]             # Tables selected by FAISS retrieval
    schema_context: str                    # Compact schema text for LLM
    total_tables: int                      # Total tables in DB
    schema_retrieval_time_ms: float

    # ── Conversation ──────────────────────────────────────────────────────────
    conversation_context: str

    # ── Planner output ────────────────────────────────────────────────────────
    plan: dict[str, Any]
    planning_time_ms: float
    ambiguity_detected: bool
    ambiguity_question: Optional[str]
    clarification_options: list[str]

    # ── SQL generation ────────────────────────────────────────────────────────
    sql: str
    sql_explanation: str
    sql_confidence: float
    sql_generation_time_ms: float

    # ── Validation ────────────────────────────────────────────────────────────
    validation_passed: bool
    validation_errors: list[str]
    validation_warnings: list[str]

    # ── Execution ─────────────────────────────────────────────────────────────
    execution_columns: list[str]
    execution_rows: list[list[Any]]
    execution_row_count: int
    execution_time_ms: float
    execution_truncated: bool
    execution_error: Optional[str]

    # ── Self-correction ───────────────────────────────────────────────────────
    retry_count: int
    sql_corrected: bool
    correction_history: list[dict[str, Any]]  # [{sql, error, attempt}]

    # ── Analytics ─────────────────────────────────────────────────────────────
    answer: str
    insights: list[str]
    trends: list[str]
    statistics: dict[str, Any]
    analytics_time_ms: float

    # ── Visualization ─────────────────────────────────────────────────────────
    visualization: Optional[dict[str, Any]]

    # ── Token tracking ────────────────────────────────────────────────────────
    input_tokens: int
    output_tokens: int

    # ── Timing ────────────────────────────────────────────────────────────────
    total_start_time: float
    total_time_ms: float

    # ── Error / status ────────────────────────────────────────────────────────
    error: Optional[str]
    status: str  # "success" | "error" | "ambiguous" | "no_results"
