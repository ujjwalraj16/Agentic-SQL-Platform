"""
agents/sql_agent.py – SQL Agent

Receives the user question, planner output, and relevant schema.
Generates a valid SQL SELECT query.

Also handles self-correction: when given a database error, it corrects the SQL.
Max 3 correction attempts (configured via MAX_SQL_RETRIES).

Output format:
{
    "sql": "SELECT ...",
    "explanation": "This query joins ...",
    "confidence": 0.92
}
"""

from __future__ import annotations
import json
import logging
import re
from typing import Any, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from app.agents.llm_factory import get_llm

logger = logging.getLogger(__name__)

SQL_AGENT_SYSTEM = """You are an expert SQL query generator. You write precise, efficient SQL queries based on natural language questions.

CRITICAL RULES:
1. Output ONLY valid JSON — no markdown, no explanation, no chain-of-thought.
2. Only use tables and columns that exist in the provided schema.
3. Never invent columns or tables not in the schema.
4. Only generate SELECT queries. Never generate DROP, DELETE, UPDATE, INSERT, etc.
5. Use proper SQL syntax for the database type specified.
6. Return valid JSON with exactly these fields: sql, explanation, confidence.
7. confidence is a float between 0.0 and 1.0.
8. The explanation should be 1-2 sentences describing what the query does.

Output schema:
{
  "sql": "<complete SQL query>",
  "explanation": "<1-2 sentence description>",
  "confidence": <0.0 to 1.0>
}
"""

SQL_CORRECTION_SYSTEM = """You are an expert SQL debugger. You fix SQL queries that have errors.

CRITICAL RULES:
1. Output ONLY valid JSON — no markdown, no chain-of-thought.
2. Only use tables and columns from the provided schema.
3. Analyze the error message carefully and fix the root cause.
4. The fix must be a SELECT query only.
5. confidence should reflect how sure you are of the fix.

Output schema:
{
  "sql": "<corrected SQL query>",
  "explanation": "<brief description of what was fixed>",
  "confidence": <0.0 to 1.0>
}
"""


class SQLAgent:
    """Agent 2: Generates and self-corrects SQL queries."""

    def __init__(self) -> None:
        self._llm = get_llm()

    def generate(
        self,
        question: str,
        plan: dict[str, Any],
        schema_context: str,
        db_type: str = "sqlite",
        conversation_context: str = "",
    ) -> dict[str, Any]:
        """
        Generate SQL from question + plan + schema.

        Returns dict with keys: sql, explanation, confidence
        """
        prompt = self._build_generation_prompt(
            question, plan, schema_context, db_type, conversation_context
        )
        return self._call_llm(SQL_AGENT_SYSTEM, prompt)

    def correct(
        self,
        question: str,
        failed_sql: str,
        error_message: str,
        schema_context: str,
        db_type: str = "sqlite",
        attempt: int = 1,
    ) -> dict[str, Any]:
        """
        Attempt to correct a SQL query given the error from the database.

        Returns corrected dict with keys: sql, explanation, confidence
        """
        prompt = self._build_correction_prompt(
            question, failed_sql, error_message, schema_context, db_type, attempt
        )
        return self._call_llm(SQL_CORRECTION_SYSTEM, prompt)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _build_generation_prompt(
        self,
        question: str,
        plan: dict[str, Any],
        schema_context: str,
        db_type: str,
        conversation_context: str,
    ) -> str:
        parts = [
            f"Database Type: {db_type}",
            f"\nSchema:\n{schema_context}",
        ]
        if conversation_context:
            parts.append(f"\n{conversation_context}")

        parts.extend([
            f"\nUser Question: {question}",
            f"\nQuery Plan: {json.dumps(plan, indent=2)}",
            "\nGenerate the SQL query JSON:",
        ])
        return "\n".join(parts)

    def _build_correction_prompt(
        self,
        question: str,
        failed_sql: str,
        error_message: str,
        schema_context: str,
        db_type: str,
        attempt: int,
    ) -> str:
        return (
            f"Database Type: {db_type}\n"
            f"\nSchema:\n{schema_context}"
            f"\nOriginal Question: {question}"
            f"\nFailed SQL:\n{failed_sql}"
            f"\nError Message: {error_message}"
            f"\nAttempt: {attempt}"
            "\nFix the SQL and return the corrected JSON:"
        )

    def _call_llm(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        try:
            response = self._llm.invoke(messages)
            return self._parse_response(response.content)
        except Exception as exc:
            logger.error("SQL agent error: %s", exc)
            return {"sql": "", "explanation": str(exc), "confidence": 0.0}

    def _parse_response(self, raw: str) -> dict[str, Any]:
        """Parse LLM JSON response, stripping CoT and markdown."""
        # Remove <think>...</think>
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        # Strip markdown fences
        raw = re.sub(r"```(?:json|sql)?\s*", "", raw).replace("```", "").strip()

        # Find JSON
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                return {
                    "sql": str(data.get("sql", "")).strip(),
                    "explanation": str(data.get("explanation", "")),
                    "confidence": float(data.get("confidence", 0.5)),
                }
            except (json.JSONDecodeError, ValueError):
                pass

        # Fallback: try to extract SQL directly
        sql_match = re.search(r"SELECT\s+.+", raw, re.IGNORECASE | re.DOTALL)
        if sql_match:
            return {
                "sql": sql_match.group().strip(),
                "explanation": "SQL extracted from response.",
                "confidence": 0.3,
            }

        return {"sql": "", "explanation": "Could not generate SQL.", "confidence": 0.0}
