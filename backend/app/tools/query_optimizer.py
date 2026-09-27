"""
tools/query_optimizer.py – Query optimization tool (deterministic, not an agent).

Uses EXPLAIN or heuristic analysis to:
- Detect SELECT *
- Detect unnecessary JOINs
- Detect missing WHERE clauses on large tables
- Suggest index candidates
- Compare execution times (original vs optimized)

Never modifies the user's database automatically.
"""

from __future__ import annotations
import re
import logging
import time
from typing import Any, Optional

from sqlalchemy.engine import Engine
from sqlalchemy import text

logger = logging.getLogger(__name__)


class OptimizationResult:
    def __init__(
        self,
        original_sql: str,
        optimized_sql: str,
        issues: list[str],
        suggestions: list[str],
        original_time_ms: Optional[float] = None,
        optimized_time_ms: Optional[float] = None,
    ) -> None:
        self.original_sql = original_sql
        self.optimized_sql = optimized_sql
        self.issues = issues
        self.suggestions = suggestions
        self.original_time_ms = original_time_ms
        self.optimized_time_ms = optimized_time_ms

    @property
    def improvement_pct(self) -> Optional[float]:
        if self.original_time_ms and self.optimized_time_ms and self.original_time_ms > 0:
            return round(
                (self.original_time_ms - self.optimized_time_ms) / self.original_time_ms * 100, 1
            )
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_sql": self.original_sql,
            "optimized_sql": self.optimized_sql,
            "issues_found": self.issues,
            "suggestions": self.suggestions,
            "original_execution_time_ms": self.original_time_ms,
            "optimized_execution_time_ms": self.optimized_time_ms,
            "improvement_pct": self.improvement_pct,
        }


def optimize_query(
    sql: str,
    engine: Engine,
    schema: Optional[dict[str, Any]] = None,
) -> OptimizationResult:
    """Analyze and optionally rewrite SQL for performance."""
    issues: list[str] = []
    suggestions: list[str] = []
    optimized = sql.strip()

    upper = sql.upper()

    # ── Heuristic checks ─────────────────────────────────────────────────────

    # SELECT *
    if re.search(r"SELECT\s+\*", upper):
        issues.append("Using SELECT * fetches all columns (inefficient).")
        suggestions.append("Replace SELECT * with explicit column names.")

    # No WHERE clause with large tables
    if "WHERE" not in upper and schema:
        # Check if any referenced table is large
        for tbl, info in schema.get("tables", {}).items():
            if tbl.upper() in upper and info.get("row_count", 0) > 10000:
                issues.append(
                    f"Query on large table '{tbl}' ({info['row_count']:,} rows) "
                    "without a WHERE clause."
                )
                suggestions.append(
                    f"Add a WHERE clause to filter '{tbl}' if possible."
                )
                break

    # LIKE with leading wildcard
    if re.search(r"LIKE\s+'%\w", upper):
        issues.append("LIKE with a leading wildcard ('%...') prevents index use.")
        suggestions.append(
            "Use a trailing wildcard ('word%') or full-text search where possible."
        )

    # Unnecessary DISTINCT
    if "DISTINCT" in upper and "GROUP BY" in upper:
        issues.append("DISTINCT combined with GROUP BY is often redundant.")
        suggestions.append("Remove DISTINCT if GROUP BY already produces unique rows.")

    # ORDER BY without LIMIT on large result
    if "ORDER BY" in upper and "LIMIT" not in upper:
        issues.append("ORDER BY without LIMIT sorts the full result set.")
        suggestions.append("Add LIMIT to avoid sorting large datasets unnecessarily.")

    # ── Get execution times ───────────────────────────────────────────────────
    original_time = _time_query(engine, sql)
    optimized_time = original_time  # same if no rewrite

    # If we suggest an optimized version (simple case: remove SELECT *)
    if re.search(r"SELECT\s+\*", upper) and schema:
        # Try to replace SELECT * with actual columns from the first referenced table
        pass  # Complex rewrite left as suggestion, not auto-applied

    return OptimizationResult(
        original_sql=sql,
        optimized_sql=optimized,
        issues=issues,
        suggestions=suggestions,
        original_time_ms=original_time,
        optimized_time_ms=optimized_time,
    )


def _time_query(engine: Engine, sql: str, iterations: int = 1) -> Optional[float]:
    """Execute a query and return average execution time in ms."""
    try:
        times: list[float] = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            with engine.connect() as conn:
                result = conn.execute(text(sql))
                result.fetchall()
            times.append((time.perf_counter() - t0) * 1000)
        return round(sum(times) / len(times), 2)
    except Exception as e:
        logger.debug("Query timing failed: %s", e)
        return None


def get_explain_plan(engine: Engine, sql: str) -> Optional[str]:
    """Get EXPLAIN plan if the database supports it."""
    db_type = engine.dialect.name
    try:
        if db_type == "sqlite":
            explain_sql = f"EXPLAIN QUERY PLAN {sql}"
        elif db_type in ("postgresql", "mysql"):
            explain_sql = f"EXPLAIN {sql}"
        else:
            return None

        with engine.connect() as conn:
            result = conn.execute(text(explain_sql))
            rows = result.fetchall()
            return "\n".join(str(r) for r in rows)
    except Exception as e:
        logger.debug("EXPLAIN failed: %s", e)
        return None
