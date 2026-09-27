"""
memory/conversation.py – Conversation memory manager.

Maintains structured state per session including:
- Previous questions
- Previous SQL
- Tables / filters / metrics used
- Time ranges
- Result summaries

Does NOT blindly dump the entire conversation to the LLM.
Instead, builds a compact context string for each new query.
"""

from __future__ import annotations
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)

MAX_HISTORY_PER_SESSION = 10


class ConversationTurn:
    def __init__(
        self,
        question: str,
        sql: str,
        tables: list[str],
        filters: list[str],
        metrics: list[str],
        time_range: Optional[str],
        result_summary: str,
    ) -> None:
        self.question = question
        self.sql = sql
        self.tables = tables
        self.filters = filters
        self.metrics = metrics
        self.time_range = time_range
        self.result_summary = result_summary
        self.timestamp = datetime.utcnow()


class ConversationMemory:
    """Per-session conversation state manager."""

    def __init__(self) -> None:
        # session_id → list of ConversationTurn
        self._sessions: dict[str, list[ConversationTurn]] = defaultdict(list)

    def add_turn(
        self,
        session_id: str,
        question: str,
        sql: str,
        tables: list[str],
        filters: list[str],
        metrics: list[str],
        time_range: Optional[str],
        result_summary: str,
    ) -> None:
        turns = self._sessions[session_id]
        turns.append(
            ConversationTurn(
                question=question,
                sql=sql,
                tables=tables,
                filters=filters,
                metrics=metrics,
                time_range=time_range,
                result_summary=result_summary,
            )
        )
        # Keep only recent history
        if len(turns) > MAX_HISTORY_PER_SESSION:
            self._sessions[session_id] = turns[-MAX_HISTORY_PER_SESSION:]

    def get_context_string(self, session_id: str) -> str:
        """
        Return a compact context string suitable for LLM injection.
        Only includes the last 3 turns to avoid token bloat.
        """
        turns = self._sessions.get(session_id, [])
        if not turns:
            return ""

        recent = turns[-3:]
        lines = ["Previous conversation context:"]
        for i, turn in enumerate(recent, 1):
            lines.append(f"\n[Turn {i}]")
            lines.append(f"  Question: {turn.question}")
            lines.append(f"  SQL: {turn.sql[:200]}{'...' if len(turn.sql) > 200 else ''}")
            lines.append(f"  Tables: {', '.join(turn.tables)}")
            if turn.filters:
                lines.append(f"  Filters: {', '.join(turn.filters)}")
            if turn.metrics:
                lines.append(f"  Metrics: {', '.join(turn.metrics)}")
            if turn.time_range:
                lines.append(f"  Time range: {turn.time_range}")
            lines.append(f"  Result: {turn.result_summary}")

        return "\n".join(lines)

    def get_last_turn(self, session_id: str) -> Optional[ConversationTurn]:
        turns = self._sessions.get(session_id, [])
        return turns[-1] if turns else None

    def clear_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


# Singleton
_memory = ConversationMemory()


def get_memory() -> ConversationMemory:
    return _memory
