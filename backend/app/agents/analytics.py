"""
agents/analytics.py – Analytics Agent

Receives the user question, SQL, and query results.
Produces:
- A concise natural-language summary/answer
- 2-4 business insights
- Basic statistics (min, max, avg, pct change)
- Trend detection
- Anomaly flagging

Does NOT hallucinate beyond the provided data.
"""

from __future__ import annotations
import json
import logging
import re
from typing import Any

import pandas as pd
import numpy as np
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm_factory import get_llm

logger = logging.getLogger(__name__)

ANALYTICS_SYSTEM = """You are a data analyst assistant. Your job is to analyze SQL query results and provide concise, accurate business insights.

CRITICAL RULES:
1. Output ONLY valid JSON — no markdown, no chain-of-thought.
2. Never hallucinate or invent information not present in the data.
3. Keep insights concise (1-2 sentences each).
4. The summary should directly answer the user's question.
5. Base all observations strictly on the provided data.

Output schema:
{
  "summary": "<direct answer to the user's question, 2-3 sentences>",
  "insights": ["<insight 1>", "<insight 2>", "<insight 3>"],
  "trends": ["<trend 1>", ...]
}
"""


class AnalyticsAgent:
    """Agent 3: Analyzes query results and generates business insights."""

    def __init__(self) -> None:
        self._llm = get_llm()

    def analyze(
        self,
        question: str,
        sql: str,
        columns: list[str],
        rows: list[list[Any]],
        plan: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze query results and return insights.

        Returns dict with: summary, insights, trends, statistics
        """
        # Compute statistics deterministically first
        statistics = self._compute_statistics(columns, rows)

        # Build compact data representation for LLM (max 50 rows)
        data_preview = self._build_data_preview(columns, rows[:50])

        prompt = self._build_prompt(question, sql, data_preview, statistics, plan)

        llm_result = self._call_llm(prompt)

        return {
            "summary": llm_result.get("summary", "Query completed successfully."),
            "insights": llm_result.get("insights", []),
            "trends": llm_result.get("trends", []),
            "statistics": statistics,
        }

    # ── Deterministic statistics ──────────────────────────────────────────────

    def _compute_statistics(
        self, columns: list[str], rows: list[list[Any]]
    ) -> dict[str, Any]:
        """Compute numeric statistics without LLM."""
        if not rows or not columns:
            return {}

        try:
            df = pd.DataFrame(rows, columns=columns)
            stats: dict[str, Any] = {"row_count": len(df)}

            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            for col in numeric_cols[:5]:  # limit to 5 numeric columns
                col_stats: dict[str, Any] = {
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "mean": round(float(df[col].mean()), 2),
                    "median": float(df[col].median()),
                    "sum": float(df[col].sum()),
                }
                # Percentage change (if time-series-like: sorted numeric index)
                if len(df) > 1:
                    pct_change = df[col].pct_change().dropna()
                    if len(pct_change) > 0:
                        col_stats["avg_pct_change"] = round(
                            float(pct_change.mean() * 100), 2
                        )
                        col_stats["max_pct_change"] = round(
                            float(pct_change.abs().max() * 100), 2
                        )
                stats[col] = col_stats

            return stats
        except Exception as e:
            logger.debug("Stats computation error: %s", e)
            return {"row_count": len(rows)}

    # ── LLM helpers ───────────────────────────────────────────────────────────

    def _build_data_preview(self, columns: list[str], rows: list[list[Any]]) -> str:
        """Create a compact table representation for the LLM prompt."""
        header = " | ".join(columns)
        sep = "-" * len(header)
        row_strs = [" | ".join(str(v) for v in row) for row in rows]
        return f"{header}\n{sep}\n" + "\n".join(row_strs[:30])

    def _build_prompt(
        self,
        question: str,
        sql: str,
        data_preview: str,
        statistics: dict[str, Any],
        plan: dict[str, Any] | None,
    ) -> str:
        parts = [
            f"User Question: {question}",
            f"\nSQL Used:\n{sql}",
            f"\nStatistics (computed):\n{json.dumps(statistics, indent=2)}",
            f"\nData Preview:\n{data_preview}",
        ]
        if plan:
            parts.append(f"\nIntent: {plan.get('intent', 'unknown')}")
        parts.append("\nGenerate the analytics JSON:")
        return "\n".join(parts)

    def _call_llm(self, user_prompt: str) -> dict[str, Any]:
        messages = [
            SystemMessage(content=ANALYTICS_SYSTEM),
            HumanMessage(content=user_prompt),
        ]
        try:
            response = self._llm.invoke(messages)
            return self._parse_response(response.content)
        except Exception as exc:
            logger.error("Analytics agent error: %s", exc)
            return {
                "summary": "Analysis could not be completed.",
                "insights": [],
                "trends": [],
            }

    def _parse_response(self, raw: str) -> dict[str, Any]:
        # Strip <think> blocks
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        # Strip markdown fences
        raw = re.sub(r"```(?:json)?\s*", "", raw).replace("```", "").strip()

        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                return {
                    "summary": str(data.get("summary", "")),
                    "insights": list(data.get("insights", [])),
                    "trends": list(data.get("trends", [])),
                }
            except json.JSONDecodeError:
                pass

        logger.warning("Could not parse analytics JSON.")
        return {"summary": raw[:500] if raw else "", "insights": [], "trends": []}
