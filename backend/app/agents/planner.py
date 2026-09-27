"""
agents/planner.py – Planner Agent

Receives the user's natural-language question and produces a structured
query plan WITHOUT exposing chain-of-thought reasoning.

Output format:
{
    "intent": "aggregation",
    "tables": ["orders", "products"],
    "operations": ["join", "group_by", "sum", "order", "limit"],
    "filters": ["year = 2025"],
    "metrics": ["revenue"],
    "limit": 5,
    "ambiguity_detected": false,
    "ambiguity_question": null,
    "clarification_options": []
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

PLANNER_SYSTEM_PROMPT = """You are a database query planning assistant. Your job is to analyze natural language questions and produce a structured query plan.

RULES:
- Output ONLY valid JSON. No explanation, no markdown, no chain-of-thought.
- Do not invent tables or columns not present in the schema.
- If the question is ambiguous, set ambiguity_detected=true and provide a clarifying question.
- Identify intent: "aggregation", "lookup", "comparison", "trend", "ranking", "filter", "join", "count", or "unknown"
- Operations can include: select, join, filter, group_by, having, order, limit, count, sum, avg, min, max, distinct, subquery, window_function, date_filter

Output schema:
{
  "intent": "<string>",
  "tables": ["<table1>", ...],
  "operations": ["<op1>", ...],
  "filters": ["<filter description>", ...],
  "metrics": ["<metric1>", ...],
  "limit": <number or null>,
  "time_range": "<description or null>",
  "ambiguity_detected": <bool>,
  "ambiguity_question": "<string or null>",
  "clarification_options": ["<option1>", ...]
}
"""


class PlannerAgent:
    """Agent 1: Understands user intent and produces a structured query plan."""

    def __init__(self) -> None:
        self._llm = get_llm()

    def plan(
        self,
        question: str,
        schema_context: str,
        conversation_context: str = "",
    ) -> dict[str, Any]:
        """
        Produce a structured query plan from the user's question.

        Args:
            question: The user's natural language question.
            schema_context: Compact schema text for relevant tables.
            conversation_context: Recent conversation turns (optional).

        Returns:
            Parsed query plan dict.
        """
        user_content = self._build_user_prompt(
            question, schema_context, conversation_context
        )

        messages = [
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]

        try:
            response = self._llm.invoke(messages)
            raw = response.content
            return self._parse_response(raw)
        except Exception as exc:
            logger.error("Planner agent error: %s", exc)
            return self._fallback_plan(question)

    def _build_user_prompt(
        self, question: str, schema_context: str, conversation_context: str
    ) -> str:
        parts = [f"Database Schema:\n{schema_context}"]
        if conversation_context:
            parts.append(f"\n{conversation_context}")
        parts.append(f"\nUser Question: {question}")
        parts.append("\nGenerate the query plan JSON:")
        return "\n".join(parts)

    def _parse_response(self, raw: str) -> dict[str, Any]:
        """Extract JSON from LLM response, stripping markdown fences if present."""
        # Remove <think>...</think> blocks (Ollama chain-of-thought)
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

        # Strip markdown code fences
        raw = re.sub(r"```(?:json)?\s*", "", raw)
        raw = raw.replace("```", "").strip()

        # Find JSON object
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                plan = json.loads(match.group())
                return self._normalize_plan(plan)
            except json.JSONDecodeError:
                pass

        logger.warning("Could not parse planner JSON, using fallback.")
        return self._fallback_plan("")

    def _normalize_plan(self, plan: dict[str, Any]) -> dict[str, Any]:
        """Ensure all required fields exist with correct types."""
        return {
            "intent": str(plan.get("intent", "unknown")),
            "tables": list(plan.get("tables", [])),
            "operations": list(plan.get("operations", [])),
            "filters": list(plan.get("filters", [])),
            "metrics": list(plan.get("metrics", [])),
            "limit": plan.get("limit"),
            "time_range": plan.get("time_range"),
            "ambiguity_detected": bool(plan.get("ambiguity_detected", False)),
            "ambiguity_question": plan.get("ambiguity_question"),
            "clarification_options": list(plan.get("clarification_options", [])),
        }

    def _fallback_plan(self, question: str) -> dict[str, Any]:
        return {
            "intent": "lookup",
            "tables": [],
            "operations": ["select"],
            "filters": [],
            "metrics": [],
            "limit": None,
            "time_range": None,
            "ambiguity_detected": False,
            "ambiguity_question": None,
            "clarification_options": [],
        }
