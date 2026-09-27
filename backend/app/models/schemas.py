"""
models/schemas.py – Pydantic request/response models for all API endpoints.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


# ── Database Connection ──────────────────────────────────────────────────────

class DatabaseConnectRequest(BaseModel):
    db_type: str = Field(..., description="Database type: sqlite | postgresql | mysql")
    host: Optional[str] = None
    port: Optional[int] = None
    database: str
    username: Optional[str] = None
    password: Optional[str] = None  # Never logged

    class Config:
        json_schema_extra = {
            "example": {
                "db_type": "sqlite",
                "database": "./data/sample.db",
            }
        }


class DatabaseConnectResponse(BaseModel):
    success: bool
    message: str
    db_type: Optional[str] = None
    database: Optional[str] = None


# ── Query ────────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    database_url: Optional[str] = None  # override current connection


class PlannerOutput(BaseModel):
    intent: str
    tables: list[str]
    operations: list[str]
    filters: list[str]
    metrics: list[str]
    limit: Optional[int] = None
    ambiguity_detected: bool = False
    ambiguity_question: Optional[str] = None
    clarification_options: list[str] = []


class SQLOutput(BaseModel):
    sql: str
    explanation: str
    confidence: float
    attempts: int = 1


class ExecutionResult(BaseModel):
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    execution_time_ms: float
    truncated: bool = False


class AnalyticsOutput(BaseModel):
    summary: str
    insights: list[str]
    statistics: dict[str, Any] = {}
    trends: list[str] = []


class VisualizationConfig(BaseModel):
    chart_type: str  # line | bar | scatter | pie | histogram | table
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    title: str
    data: list[dict[str, Any]]
    color_scheme: str = "blue"


class PerformanceMetrics(BaseModel):
    execution_time_ms: float
    planning_time_ms: float
    total_time_ms: float
    retries: int
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    schema_tables_retrieved: int
    schema_total_tables: int


class QueryResponse(BaseModel):
    query_id: str
    question: str
    answer: str
    planner: PlannerOutput
    sql_output: SQLOutput
    execution: ExecutionResult
    analytics: AnalyticsOutput
    visualization: Optional[VisualizationConfig] = None
    performance: PerformanceMetrics
    sql_corrected: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── Schema ───────────────────────────────────────────────────────────────────

class ColumnInfo(BaseModel):
    name: str
    type: str
    nullable: bool
    primary_key: bool
    foreign_key: Optional[str] = None
    sample_values: list[Any] = []


class TableInfo(BaseModel):
    name: str
    row_count: int
    columns: list[ColumnInfo]
    relationships: list[str] = []


class SchemaResponse(BaseModel):
    database: str
    db_type: str
    tables: list[TableInfo]
    total_tables: int


# ── History ──────────────────────────────────────────────────────────────────

class HistoryItem(BaseModel):
    query_id: str
    question: str
    sql: str
    timestamp: datetime
    execution_time_ms: float
    success: bool
    retries: int
    row_count: int


class HistoryResponse(BaseModel):
    items: list[HistoryItem]
    total: int


# ── Metrics ──────────────────────────────────────────────────────────────────

class MetricsResponse(BaseModel):
    total_queries: int
    successful_queries: int
    failed_queries: int
    sql_success_rate: float
    self_correction_rate: float
    avg_latency_ms: float
    avg_execution_time_ms: float
    avg_retries: float
    total_input_tokens: int
    total_output_tokens: int
    estimated_cost_usd: float
    schema_retrieval_avg_tables: float
    schema_total_avg_tables: float
    token_reduction_pct: float


# ── Optimization ─────────────────────────────────────────────────────────────

class OptimizeRequest(BaseModel):
    sql: str
    query_id: Optional[str] = None


class OptimizationResult(BaseModel):
    original_sql: str
    optimized_sql: str
    issues_found: list[str]
    suggestions: list[str]
    original_execution_time_ms: Optional[float] = None
    optimized_execution_time_ms: Optional[float] = None
    improvement_pct: Optional[float] = None


# ── Ambiguity ────────────────────────────────────────────────────────────────

class ClarifyRequest(BaseModel):
    session_id: str
    clarification: str
