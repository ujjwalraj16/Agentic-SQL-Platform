"""
main.py – FastAPI application entry point.

All API routes for the Agentic SQL Intelligence Platform.
"""

from __future__ import annotations
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.connection import DatabaseManager
from app.database.schema import extract_full_schema, schema_to_compact_text
from app.graph.workflow import get_workflow
from app.graph.state import AgentState
from app.models.schemas import (
    DatabaseConnectRequest,
    DatabaseConnectResponse,
    QueryRequest,
    QueryResponse,
    SchemaResponse,
    TableInfo,
    ColumnInfo,
    HistoryResponse,
    MetricsResponse,
    OptimizeRequest,
    OptimizationResult,
)
from app.services.history import get_history_service
from app.services.metrics import get_metrics_service
from app.tools.query_optimizer import optimize_query
from app.retrieval.vector_store import get_vector_store

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


# ── Lifespan ───────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: connect to default database."""
    logger.info("Starting Agentic SQL Intelligence Platform...")
    try:
        DatabaseManager.connect(settings.database_url)
        logger.info("Default database connected: %s", settings.database_url)
        # Pre-build FAISS index
        engine = DatabaseManager.get_engine()
        schema = extract_full_schema(engine)
        vs = get_vector_store()
        vs.build_from_schema(schema)
        logger.info("FAISS schema index built.")
    except Exception as e:
        logger.warning("Startup DB connection failed (will require manual connect): %s", e)

    yield

    logger.info("Shutting down...")
    DatabaseManager.dispose()


# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Agentic SQL Intelligence Platform",
    version="1.0.0",
    description="Natural language to SQL with 3 AI agents: Planner → SQL → Analytics",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "db_connected": DatabaseManager.is_connected(),
        "db_type": DatabaseManager.get_db_type(),
        "llm_provider": settings.llm_provider,
    }


# ── Database ───────────────────────────────────────────────────────────────────

@app.post("/api/database/test", response_model=DatabaseConnectResponse)
async def test_database(request: DatabaseConnectRequest):
    """Test a database connection without saving it."""
    url = _build_database_url(request)
    success, message = DatabaseManager.test_connection(url)
    return DatabaseConnectResponse(
        success=success,
        message=message,
        db_type=request.db_type,
        database=request.database,
    )


@app.post("/api/database/connect", response_model=DatabaseConnectResponse)
async def connect_database(request: DatabaseConnectRequest):
    """Connect to a database and rebuild the schema index."""
    url = _build_database_url(request)

    # Test first
    success, message = DatabaseManager.test_connection(url)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    # Connect
    DatabaseManager.connect(url)

    # Rebuild FAISS index
    try:
        engine = DatabaseManager.get_engine()
        schema = extract_full_schema(engine)
        vs = get_vector_store()
        vs.build_from_schema(schema)
        logger.info("Schema index rebuilt for new connection.")
    except Exception as e:
        logger.warning("Schema index rebuild failed: %s", e)

    return DatabaseConnectResponse(
        success=True,
        message=f"Connected to {request.db_type} database '{request.database}' successfully.",
        db_type=request.db_type,
        database=request.database,
    )


def _build_database_url(req: DatabaseConnectRequest) -> str:
    """Build a SQLAlchemy URL from the connection request."""
    if req.db_type == "sqlite":
        db_path = req.database
        if not db_path.startswith("/") and not db_path.startswith("."):
            db_path = f"./{db_path}"
        return f"sqlite:///{db_path}"
    elif req.db_type == "postgresql":
        user = req.username or "postgres"
        pw = req.password or ""
        host = req.host or "localhost"
        port = req.port or 5432
        return f"postgresql://{user}:{pw}@{host}:{port}/{req.database}"
    elif req.db_type == "mysql":
        user = req.username or "root"
        pw = req.password or ""
        host = req.host or "localhost"
        port = req.port or 3306
        return f"mysql+pymysql://{user}:{pw}@{host}:{port}/{req.database}"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported database type: {req.db_type}")


# ── Schema ─────────────────────────────────────────────────────────────────────

@app.get("/api/schema", response_model=SchemaResponse)
async def get_schema():
    """Return the full database schema."""
    if not DatabaseManager.is_connected():
        raise HTTPException(status_code=503, detail="No database connected.")

    engine = DatabaseManager.get_engine()
    raw_schema = extract_full_schema(engine)

    tables = []
    for tbl_name, tbl_info in raw_schema["tables"].items():
        columns = [
            ColumnInfo(
                name=col["name"],
                type=col["type"],
                nullable=col["nullable"],
                primary_key=col["primary_key"],
                foreign_key=col.get("foreign_key"),
                sample_values=col.get("sample_values", []),
            )
            for col in tbl_info["columns"]
        ]
        tables.append(
            TableInfo(
                name=tbl_name,
                row_count=tbl_info["row_count"],
                columns=columns,
                relationships=tbl_info.get("relationships", []),
            )
        )

    return SchemaResponse(
        database=raw_schema["database"],
        db_type=raw_schema["db_type"],
        tables=tables,
        total_tables=len(tables),
    )


# ── Query ──────────────────────────────────────────────────────────────────────

@app.post("/api/query")
async def run_query(request: QueryRequest):
    """
    Main endpoint: run the agentic workflow for a natural-language question.
    Returns full structured response including SQL, data, analytics, and visualization.
    """
    if not DatabaseManager.is_connected():
        raise HTTPException(status_code=503, detail="No database connected.")

    query_id = str(uuid.uuid4())
    session_id = request.session_id or "default"
    t_start = time.perf_counter()

    # Build initial state
    initial_state: AgentState = {
        "question": request.question,
        "session_id": session_id,
        "query_id": query_id,
        "retry_count": 0,
        "sql_corrected": False,
        "correction_history": [],
        "input_tokens": 0,
        "output_tokens": 0,
        "total_start_time": t_start,
    }

    # Run workflow
    try:
        workflow = get_workflow()
        final_state: AgentState = await _run_graph(workflow, initial_state)
    except Exception as exc:
        logger.error("Workflow error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your query.",
        )

    total_ms = (time.perf_counter() - t_start) * 1000
    success = final_state.get("status") == "success"

    # Record metrics
    get_metrics_service().record(
        success=success,
        latency_ms=total_ms,
        execution_time_ms=final_state.get("execution_time_ms", 0),
        retries=final_state.get("retry_count", 0),
        input_tokens=final_state.get("input_tokens", 0),
        output_tokens=final_state.get("output_tokens", 0),
        schema_tables_retrieved=len(final_state.get("relevant_tables", [])),
        schema_total_tables=final_state.get("total_tables", 0),
        sql_corrected=final_state.get("sql_corrected", False),
    )

    # Record history
    get_history_service().add(
        query_id=query_id,
        question=request.question,
        sql=final_state.get("sql", ""),
        execution_time_ms=final_state.get("execution_time_ms", 0),
        success=success,
        retries=final_state.get("retry_count", 0),
        row_count=final_state.get("execution_row_count", 0),
    )

    # Build response
    return _build_response(query_id, request.question, final_state, total_ms)


async def _run_graph(workflow, state: AgentState) -> AgentState:
    """Run the LangGraph workflow (synchronous invoke wrapped for FastAPI)."""
    import asyncio
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, workflow.invoke, state)
    return result


def _build_response(
    query_id: str,
    question: str,
    state: AgentState,
    total_ms: float,
) -> dict[str, Any]:
    plan = state.get("plan", {})
    exec_result = {
        "columns": state.get("execution_columns", []),
        "rows": state.get("execution_rows", []),
        "row_count": state.get("execution_row_count", 0),
        "execution_time_ms": round(state.get("execution_time_ms", 0), 2),
        "truncated": state.get("execution_truncated", False),
    }

    return {
        "query_id": query_id,
        "question": question,
        "status": state.get("status", "error"),
        "answer": state.get("answer", ""),
        "sql_corrected": state.get("sql_corrected", False),
        "ambiguity_detected": state.get("ambiguity_detected", False),
        "clarification_options": state.get("clarification_options", []),
        "planner": plan,
        "sql_output": {
            "sql": state.get("sql", ""),
            "explanation": state.get("sql_explanation", ""),
            "confidence": state.get("sql_confidence", 0.0),
            "attempts": state.get("retry_count", 0) + 1,
            "warnings": state.get("validation_warnings", []),
        },
        "execution": exec_result,
        "analytics": {
            "summary": state.get("answer", ""),
            "insights": state.get("insights", []),
            "trends": state.get("trends", []),
            "statistics": state.get("statistics", {}),
        },
        "visualization": state.get("visualization"),
        "performance": {
            "execution_time_ms": round(state.get("execution_time_ms", 0), 2),
            "planning_time_ms": round(state.get("planning_time_ms", 0), 2),
            "total_time_ms": round(total_ms, 2),
            "retries": state.get("retry_count", 0),
            "input_tokens": state.get("input_tokens", 0),
            "output_tokens": state.get("output_tokens", 0),
            "schema_tables_retrieved": len(state.get("relevant_tables", [])),
            "schema_total_tables": state.get("total_tables", 0),
        },
    }


# ── Query optimization ─────────────────────────────────────────────────────────

@app.post("/api/query/optimize")
async def optimize_query_endpoint(request: OptimizeRequest):
    """Analyze and optimize a SQL query."""
    if not DatabaseManager.is_connected():
        raise HTTPException(status_code=503, detail="No database connected.")

    engine = DatabaseManager.get_engine()
    schema = extract_full_schema(engine)

    import asyncio
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: optimize_query(request.sql, engine, schema),
    )
    return result.to_dict()


# ── History ────────────────────────────────────────────────────────────────────

@app.get("/api/history", response_model=HistoryResponse)
async def get_history(limit: int = 50):
    svc = get_history_service()
    items = svc.get_all(limit=limit)
    return HistoryResponse(items=items, total=svc.total())


@app.get("/api/history/{query_id}")
async def get_query_by_id(query_id: str):
    item = get_history_service().get_by_id(query_id)
    if not item:
        raise HTTPException(status_code=404, detail="Query not found.")
    return item


@app.delete("/api/history")
async def clear_history():
    """Clear all history."""
    svc = get_history_service()
    svc.clear()
    return {"success": True, "message": "History cleared."}


@app.delete("/api/history/{query_id}")
async def delete_history_item(query_id: str):
    """Delete a single history item by ID."""
    svc = get_history_service()
    deleted = svc.delete(query_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found.")
    return {"success": True, "message": "Item deleted."}


# ── Metrics ────────────────────────────────────────────────────────────────────

@app.get("/api/metrics")
async def get_metrics():
    return get_metrics_service().compute()


# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
    )
