"""
services/history.py – Query history service.

Stores query history in memory (for demo) with a limit.
In production, this would persist to a database table.
"""

from __future__ import annotations
import logging
from collections import deque
from datetime import datetime
from typing import Optional
from app.models.schemas import HistoryItem

logger = logging.getLogger(__name__)

MAX_HISTORY = 500


class HistoryService:
    def __init__(self) -> None:
        self._history: deque[HistoryItem] = deque(maxlen=MAX_HISTORY)
        self._by_id: dict[str, HistoryItem] = {}

    def add(
        self,
        query_id: str,
        question: str,
        sql: str,
        execution_time_ms: float,
        success: bool,
        retries: int,
        row_count: int,
    ) -> None:
        item = HistoryItem(
            query_id=query_id,
            question=question,
            sql=sql,
            timestamp=datetime.utcnow(),
            execution_time_ms=execution_time_ms,
            success=success,
            retries=retries,
            row_count=row_count,
        )
        self._history.appendleft(item)
        self._by_id[query_id] = item

    def get_all(self, limit: int = 50) -> list[HistoryItem]:
        return list(self._history)[:limit]

    def get_by_id(self, query_id: str) -> Optional[HistoryItem]:
        return self._by_id.get(query_id)

    def total(self) -> int:
        return len(self._history)


_history_service = HistoryService()


def get_history_service() -> HistoryService:
    return _history_service
