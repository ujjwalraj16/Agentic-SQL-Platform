"""
graph/workflow.py – LangGraph agentic workflow.

Graph structure:
    START
    ↓
    retrieve_schema       (FAISS schema retrieval)
    ↓
    plan                  (Planner Agent)
    ↓
    [ambiguity check] ──→ END (if ambiguous)
    ↓
    generate_sql          (SQL Agent)
    ↓
    validate_sql          (deterministic validator)
    ↓
    [validation check] ──→ correct_sql → validate_sql (loop, max retries)
    ↓
    execute_sql           (SQL executor)
    ↓
    [execution check] ──→ correct_sql → validate_sql → execute_sql (loop)
    ↓
    analyze               (Analytics Agent)
    ↓
    visualize             (deterministic chart selector)
    ↓
    END
"""

from __future__ import annotations
import logging
import time
import uuid
from typing import Any, Literal

from langgraph.graph import StateGraph, START, END

from app.graph.state import AgentState
from app.agents.planner import PlannerAgent
from app.agents.sql_agent import SQLAgent
from app.agents.analytics import AnalyticsAgent
from app.tools.sql_validator import validate_sql
from app.tools.sql_executor import execute_sql
from app.tools.visualization import determine_visualization
from app.database.connection import DatabaseManager
from app.database.schema import extract_full_schema, schema_to_compact_text
from app.retrieval.vector_store import get_vector_store
from app.memory.conversation import get_memory
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Singletons (loaded once)
_planner = PlannerAgent()
_sql_agent = SQLAgent()
_analytics = AnalyticsAgent()


# ── Node implementations ──────────────────────────────────────────────────────

def node_retrieve_schema(state: AgentState) -> AgentState:
    """Retrieve full schema and select relevant tables via FAISS."""
    t0 = time.perf_counter()

    engine = DatabaseManager.get_engine()
    full_schema = extract_full_schema(engine)

    vector_store = get_vector_store()
    if vector_store.get_total_tables() == 0:
        vector_store.build_from_schema(full_schema)

    question = state["question"]
    relevant_tables, retrieval_ms = vector_store.retrieve_relevant_tables(question)
    schema_context = schema_to_compact_text(full_schema, relevant_tables)

    # Conversation context
    session_id = state.get("session_id", "default")
    conv_context = get_memory().get_context_string(session_id)

    logger.info(
        "Schema retrieval: %d/%d tables, %.1fms",
        len(relevant_tables),
        len(full_schema["tables"]),
        retrieval_ms,
    )

    return {
        **state,
        "schema": full_schema,
        "relevant_tables": relevant_tables,
        "schema_context": schema_context,
        "total_tables": len(full_schema["tables"]),
        "schema_retrieval_time_ms": retrieval_ms,
        "conversation_context": conv_context,
        "retry_count": state.get("retry_count", 0),
        "sql_corrected": state.get("sql_corrected", False),
        "correction_history": state.get("correction_history", []),
        "input_tokens": state.get("input_tokens", 0),
        "output_tokens": state.get("output_tokens", 0),
        "total_start_time": state.get("total_start_time", t0),
    }


def node_plan(state: AgentState) -> AgentState:
    """Planner Agent: produce structured query plan."""
    t0 = time.perf_counter()

    plan = _planner.plan(
        question=state["question"],
        schema_context=state["schema_context"],
        conversation_context=state.get("conversation_context", ""),
    )

    planning_ms = (time.perf_counter() - t0) * 1000
    logger.info("Plan: intent=%s, tables=%s", plan["intent"], plan["tables"])

    return {
        **state,
        "plan": plan,
        "planning_time_ms": planning_ms,
        "ambiguity_detected": plan.get("ambiguity_detected", False),
        "ambiguity_question": plan.get("ambiguity_question"),
        "clarification_options": plan.get("clarification_options", []),
    }


def node_generate_sql(state: AgentState) -> AgentState:
    """SQL Agent: generate SQL from plan + schema."""
    t0 = time.perf_counter()

    result = _sql_agent.generate(
        question=state["question"],
        plan=state["plan"],
        schema_context=state["schema_context"],
        db_type=DatabaseManager.get_db_type(),
        conversation_context=state.get("conversation_context", ""),
    )

    gen_ms = (time.perf_counter() - t0) * 1000
    logger.info("SQL generated (confidence=%.2f): %.200s", result["confidence"], result["sql"])

    return {
        **state,
        "sql": result["sql"],
        "sql_explanation": result["explanation"],
        "sql_confidence": result["confidence"],
        "sql_generation_time_ms": gen_ms,
    }


def node_validate_sql(state: AgentState) -> AgentState:
    """Deterministic SQL validation."""
    sql = state.get("sql", "")
    schema = state.get("schema", {})

    result = validate_sql(sql, schema)
    logger.info(
        "Validation: valid=%s errors=%s warnings=%s",
        result.valid,
        result.errors,
        result.warnings,
    )

    return {
        **state,
        "validation_passed": result.valid,
        "validation_errors": result.errors,
        "validation_warnings": result.warnings,
    }


def node_correct_sql(state: AgentState) -> AgentState:
    """SQL Agent self-correction on validation or execution error."""
    retry_count = state.get("retry_count", 0) + 1
    logger.info("SQL self-correction attempt %d", retry_count)

    # Determine the error to fix
    if state.get("execution_error"):
        error_msg = state["execution_error"]
    else:
        error_msg = "; ".join(state.get("validation_errors", []))

    result = _sql_agent.correct(
        question=state["question"],
        failed_sql=state.get("sql", ""),
        error_message=error_msg,
        schema_context=state["schema_context"],
        db_type=DatabaseManager.get_db_type(),
        attempt=retry_count,
    )

    history = state.get("correction_history", [])
    history.append({
        "attempt": retry_count,
        "failed_sql": state.get("sql", ""),
        "error": error_msg,
        "corrected_sql": result["sql"],
    })

    logger.info("Corrected SQL: %.200s", result["sql"])

    return {
        **state,
        "sql": result["sql"],
        "sql_explanation": result["explanation"],
        "sql_confidence": result["confidence"],
        "retry_count": retry_count,
        "sql_corrected": True,
        "correction_history": history,
        "execution_error": None,  # Reset error for next attempt
    }


def node_execute_sql(state: AgentState) -> AgentState:
    """Execute validated SQL against the database."""
    engine = DatabaseManager.get_engine()
    sql = state.get("sql", "")

    result = execute_sql(engine, sql, max_rows=settings.max_query_rows)

    if result.success:
        logger.info(
            "SQL executed: %d rows, %.1fms",
            result.row_count,
            result.execution_time_ms,
        )
    else:
        logger.warning("SQL execution error: %s", result.error)

    return {
        **state,
        "execution_columns": result.columns,
        "execution_rows": result.rows,
        "execution_row_count": result.row_count,
        "execution_time_ms": result.execution_time_ms,
        "execution_truncated": result.truncated,
        "execution_error": result.error,
    }


def node_analyze(state: AgentState) -> AgentState:
    """Analytics Agent: generate insights from results."""
    t0 = time.perf_counter()

    analysis = _analytics.analyze(
        question=state["question"],
        sql=state.get("sql", ""),
        columns=state.get("execution_columns", []),
        rows=state.get("execution_rows", []),
        plan=state.get("plan"),
    )

    analytics_ms = (time.perf_counter() - t0) * 1000

    # Determine status
    rows = state.get("execution_rows", [])
    status = "success" if rows else "no_results"

    return {
        **state,
        "answer": analysis["summary"],
        "insights": analysis["insights"],
        "trends": analysis["trends"],
        "statistics": analysis["statistics"],
        "analytics_time_ms": analytics_ms,
        "status": status,
    }


def node_visualize(state: AgentState) -> AgentState:
    """Deterministic visualization selection."""
    columns = state.get("execution_columns", [])
    rows = state.get("execution_rows", [])

    viz = determine_visualization(columns, rows)

    # Compute total time
    start = state.get("total_start_time", time.perf_counter())
    total_ms = (time.perf_counter() - start) * 1000

    # Update conversation memory
    session_id = state.get("session_id", "default")
    plan = state.get("plan", {})
    result_summary = f"{state.get('execution_row_count', 0)} rows returned."
    if state.get("answer"):
        result_summary = state["answer"][:200]

    get_memory().add_turn(
        session_id=session_id,
        question=state["question"],
        sql=state.get("sql", ""),
        tables=plan.get("tables", []),
        filters=plan.get("filters", []),
        metrics=plan.get("metrics", []),
        time_range=plan.get("time_range"),
        result_summary=result_summary,
    )

    return {
        **state,
        "visualization": viz,
        "total_time_ms": total_ms,
        "status": state.get("status", "success"),
    }


def node_handle_ambiguity(state: AgentState) -> AgentState:
    """Handle ambiguous queries — set status and return early."""
    return {
        **state,
        "status": "ambiguous",
        "answer": state.get("ambiguity_question", "Please clarify your question."),
        "total_time_ms": 0.0,
    }


def node_handle_error(state: AgentState) -> AgentState:
    """Handle unrecoverable errors."""
    errors = state.get("validation_errors", [])
    exec_error = state.get("execution_error", "")

    if errors and any("Blocked operation" in e for e in errors):
        msg = (
            "This operation is not permitted. "
            "The system operates in read-only mode. "
            "Only SELECT queries are allowed."
        )
    elif exec_error:
        msg = f"The query could not be executed after {state.get('retry_count', 0)} attempt(s). {exec_error}"
    else:
        msg = "An error occurred while processing your request."

    return {
        **state,
        "status": "error",
        "answer": msg,
        "insights": [],
        "trends": [],
        "statistics": {},
        "total_time_ms": 0.0,
    }


# ── Edge conditions ───────────────────────────────────────────────────────────

def should_handle_ambiguity(state: AgentState) -> Literal["handle_ambiguity", "generate_sql"]:
    if state.get("ambiguity_detected"):
        return "handle_ambiguity"
    return "generate_sql"


def after_validation(state: AgentState) -> Literal["execute_sql", "correct_sql", "handle_error"]:
    if state.get("validation_passed"):
        return "execute_sql"
    # Check if it's a blocked operation (unrecoverable)
    errors = state.get("validation_errors", [])
    if any("Blocked operation" in e or "read-only" in e for e in errors):
        return "handle_error"
    # Check retry limit
    if state.get("retry_count", 0) >= settings.max_sql_retries:
        return "handle_error"
    return "correct_sql"


def after_execution(state: AgentState) -> Literal["analyze", "correct_sql", "handle_error"]:
    if not state.get("execution_error"):
        return "analyze"
    # Retry if within limit
    if state.get("retry_count", 0) < settings.max_sql_retries:
        return "correct_sql"
    return "handle_error"


# ── Graph builder ─────────────────────────────────────────────────────────────

def build_workflow() -> Any:
    """Construct and compile the LangGraph state machine."""
    graph = StateGraph(AgentState)

    # Nodes
    graph.add_node("retrieve_schema", node_retrieve_schema)
    graph.add_node("plan", node_plan)
    graph.add_node("handle_ambiguity", node_handle_ambiguity)
    graph.add_node("generate_sql", node_generate_sql)
    graph.add_node("validate_sql", node_validate_sql)
    graph.add_node("correct_sql", node_correct_sql)
    graph.add_node("execute_sql", node_execute_sql)
    graph.add_node("analyze", node_analyze)
    graph.add_node("visualize", node_visualize)
    graph.add_node("handle_error", node_handle_error)

    # Edges
    graph.add_edge(START, "retrieve_schema")
    graph.add_edge("retrieve_schema", "plan")

    graph.add_conditional_edges(
        "plan",
        should_handle_ambiguity,
        {"handle_ambiguity": "handle_ambiguity", "generate_sql": "generate_sql"},
    )

    graph.add_edge("handle_ambiguity", END)
    graph.add_edge("generate_sql", "validate_sql")

    graph.add_conditional_edges(
        "validate_sql",
        after_validation,
        {
            "execute_sql": "execute_sql",
            "correct_sql": "correct_sql",
            "handle_error": "handle_error",
        },
    )

    graph.add_edge("correct_sql", "validate_sql")

    graph.add_conditional_edges(
        "execute_sql",
        after_execution,
        {
            "analyze": "analyze",
            "correct_sql": "correct_sql",
            "handle_error": "handle_error",
        },
    )

    graph.add_edge("analyze", "visualize")
    graph.add_edge("visualize", END)
    graph.add_edge("handle_error", END)

    return graph.compile()


# Singleton compiled graph
_compiled_graph = None


def get_workflow():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_workflow()
    return _compiled_graph
