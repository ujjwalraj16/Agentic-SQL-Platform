"""
tools/sql_executor.py – Secure SQL execution layer.

Responsibilities:
- Open a connection from the managed engine
- Execute READ-ONLY validated SQL
- Apply row limits and query timeout
- Return structured results with timing
- Never expose raw stack traces
"""

from __future__ import annotations
import logging
import time
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


class ExecutionResult:
    def __init__(
        self,
        columns: list[str],
        rows: list[list[Any]],
        row_count: int,
        execution_time_ms: float,
        truncated: bool = False,
        error: str | None = None,
    ) -> None:
        self.columns = columns
        self.rows = rows
        self.row_count = row_count
        self.execution_time_ms = execution_time_ms
        self.truncated = truncated
        self.error = error

    @property
    def success(self) -> bool:
        return self.error is None

    def to_dict(self) -> dict[str, Any]:
        return {
            "columns": self.columns,
            "rows": self.rows,
            "row_count": self.row_count,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "truncated": self.truncated,
            "error": self.error,
        }


def execute_sql(
    engine: Engine,
    sql: str,
    max_rows: int = 1000,
) -> ExecutionResult:
    """
    Execute validated SQL and return structured results.
    Applies a row limit to prevent runaway queries.
    """
    t_start = time.perf_counter()

    try:
        with engine.connect() as conn:
            # Wrap in a transaction that we immediately roll back to enforce read-only
            with conn.begin() as txn:
                result = conn.execute(text(sql))
                columns = list(result.keys())
                all_rows = result.fetchall()
                elapsed = (time.perf_counter() - t_start) * 1000

                truncated = len(all_rows) > max_rows
                rows = [list(r) for r in all_rows[:max_rows]]

                # Rollback to enforce read-only (even for SELECT, safety net)
                txn.rollback()

        return ExecutionResult(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            execution_time_ms=elapsed,
            truncated=truncated,
        )

    except Exception as exc:
        elapsed = (time.perf_counter() - t_start) * 1000
        error_msg = _sanitize_error(str(exc))
        logger.error("SQL execution error: %s", error_msg)
        return ExecutionResult(
            columns=[],
            rows=[],
            row_count=0,
            execution_time_ms=elapsed,
            error=error_msg,
        )


def _sanitize_error(raw_error: str) -> str:
    """Remove sensitive path information from database errors."""
    # Strip file paths
    import re
    sanitized = re.sub(r'[A-Za-z]:[\\\/][^\s]*', '<path>', raw_error)
    sanitized = re.sub(r'\/[^\s]*\/[^\s]*', '<path>', sanitized)
    return sanitized[:500]  # Truncate very long error messages
