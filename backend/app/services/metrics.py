"""
services/metrics.py – Real-time metrics tracker.

Computes metrics from actual application logs (not hard-coded values).
Tracks: success rate, correction rate, latency, token usage, schema efficiency.
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# Rough token cost estimate (per 1K tokens) for display purposes
COST_PER_1K_INPUT = 0.0001   # generic estimate
COST_PER_1K_OUTPUT = 0.0002


@dataclass
class QueryRecord:
    success: bool
    latency_ms: float
    execution_time_ms: float
    retries: int
    input_tokens: int
    output_tokens: int
    schema_tables_retrieved: int
    schema_total_tables: int
    sql_corrected: bool


class MetricsService:
    def __init__(self) -> None:
        self._records: list[QueryRecord] = []

    def record(
        self,
        success: bool,
        latency_ms: float,
        execution_time_ms: float,
        retries: int,
        input_tokens: int,
        output_tokens: int,
        schema_tables_retrieved: int,
        schema_total_tables: int,
        sql_corrected: bool,
    ) -> None:
        self._records.append(
            QueryRecord(
                success=success,
                latency_ms=latency_ms,
                execution_time_ms=execution_time_ms,
                retries=retries,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                schema_tables_retrieved=schema_tables_retrieved,
                schema_total_tables=schema_total_tables,
                sql_corrected=sql_corrected,
            )
        )

    def compute(self) -> dict:
        if not self._records:
            return self._empty_metrics()

        n = len(self._records)
        successes = sum(1 for r in self._records if r.success)
        corrections = sum(1 for r in self._records if r.sql_corrected)
        retried = sum(1 for r in self._records if r.retries > 0)

        total_input = sum(r.input_tokens for r in self._records)
        total_output = sum(r.output_tokens for r in self._records)

        # Schema efficiency
        retrieval_avgs = [r.schema_tables_retrieved for r in self._records if r.schema_total_tables > 0]
        total_avgs = [r.schema_total_tables for r in self._records if r.schema_total_tables > 0]
        schema_retrieved_avg = sum(retrieval_avgs) / len(retrieval_avgs) if retrieval_avgs else 0
        schema_total_avg = sum(total_avgs) / len(total_avgs) if total_avgs else 0

        # Token reduction vs sending full schema
        if schema_total_avg > 0:
            token_reduction_pct = round(
                (1 - schema_retrieved_avg / schema_total_avg) * 100, 1
            )
        else:
            token_reduction_pct = 0.0

        # Cost estimate
        estimated_cost = (total_input / 1000 * COST_PER_1K_INPUT) + (
            total_output / 1000 * COST_PER_1K_OUTPUT
        )

        return {
            "total_queries": n,
            "successful_queries": successes,
            "failed_queries": n - successes,
            "sql_success_rate": round(successes / n * 100, 1),
            "self_correction_rate": round(corrections / n * 100, 1),
            "avg_latency_ms": round(
                sum(r.latency_ms for r in self._records) / n, 1
            ),
            "avg_execution_time_ms": round(
                sum(r.execution_time_ms for r in self._records) / n, 1
            ),
            "avg_retries": round(
                sum(r.retries for r in self._records) / n, 2
            ),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "estimated_cost_usd": round(estimated_cost, 4),
            "schema_retrieval_avg_tables": round(schema_retrieved_avg, 1),
            "schema_total_avg_tables": round(schema_total_avg, 1),
            "token_reduction_pct": token_reduction_pct,
        }

    def _empty_metrics(self) -> dict:
        return {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "sql_success_rate": 0.0,
            "self_correction_rate": 0.0,
            "avg_latency_ms": 0.0,
            "avg_execution_time_ms": 0.0,
            "avg_retries": 0.0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "estimated_cost_usd": 0.0,
            "schema_retrieval_avg_tables": 0.0,
            "schema_total_avg_tables": 0.0,
            "token_reduction_pct": 0.0,
        }


_metrics_service = MetricsService()


def get_metrics_service() -> MetricsService:
    return _metrics_service
