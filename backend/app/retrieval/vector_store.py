"""
retrieval/vector_store.py – FAISS-backed schema retrieval.

Builds documents from the extracted schema and indexes them with FAISS.
At query time, retrieves the most relevant tables for a given question.
This reduces the schema sent to the LLM (token efficiency).
"""

from __future__ import annotations
import json
import logging
import os
import time
from typing import Any

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.retrieval.embeddings import get_embedding_model
from app.config import get_settings

logger = logging.getLogger(__name__)

# How many table documents to retrieve
TOP_K_TABLES = 6


class SchemaVectorStore:
    """FAISS vector store for schema documents."""

    def __init__(self) -> None:
        self._store: FAISS | None = None
        self._schema_snapshot: dict[str, Any] = {}
        self._total_tables: int = 0

    # ── Build ─────────────────────────────────────────────────────────────

    def build_from_schema(self, schema: dict[str, Any]) -> None:
        """Index all tables from the extracted schema."""
        docs: list[Document] = []
        self._schema_snapshot = schema
        self._total_tables = len(schema["tables"])

        for table_name, info in schema["tables"].items():
            # Build a rich text document for each table
            col_descs = []
            for col in info["columns"]:
                flags = []
                if col["primary_key"]:
                    flags.append("primary key")
                if col["foreign_key"]:
                    flags.append(f"references {col['foreign_key']}")
                flag_str = f" ({', '.join(flags)})" if flags else ""
                samples = col.get("sample_values", [])[:3]
                sample_str = f", examples: {samples}" if samples else ""
                col_descs.append(f"{col['name']} ({col['type']}{flag_str}{sample_str})")

            relationships = info.get("relationships", [])
            content = (
                f"Table: {table_name}\n"
                f"Rows: {info['row_count']:,}\n"
                f"Columns: {'; '.join(col_descs)}\n"
                f"Relationships: {'; '.join(relationships) or 'none'}\n"
            )
            docs.append(
                Document(
                    page_content=content,
                    metadata={
                        "table": table_name,
                        "row_count": info["row_count"],
                    },
                )
            )

        if not docs:
            logger.warning("No schema documents to index.")
            return

        embeddings = get_embedding_model()
        self._store = FAISS.from_documents(docs, embeddings)
        logger.info("FAISS index built with %d table documents.", len(docs))

    # ── Retrieve ─────────────────────────────────────────────────────────

    def retrieve_relevant_tables(
        self, question: str, k: int = TOP_K_TABLES
    ) -> tuple[list[str], float]:
        """
        Return (table_names, retrieval_time_ms) for the most relevant tables.
        Falls back to all tables if the store isn't built.
        """
        t0 = time.perf_counter()

        if self._store is None:
            all_tables = list(self._schema_snapshot.get("tables", {}).keys())
            elapsed = (time.perf_counter() - t0) * 1000
            return all_tables, elapsed

        results = self._store.similarity_search(question, k=k)
        tables = [doc.metadata["table"] for doc in results]
        elapsed = (time.perf_counter() - t0) * 1000
        logger.info(
            "Schema retrieval: %d/%d tables in %.1f ms",
            len(tables),
            self._total_tables,
            elapsed,
        )
        return tables, elapsed

    def get_total_tables(self) -> int:
        return self._total_tables

    def save(self, path: str) -> None:
        """Persist FAISS index to disk."""
        if self._store:
            os.makedirs(path, exist_ok=True)
            self._store.save_local(path)
            schema_path = os.path.join(path, "schema_snapshot.json")
            with open(schema_path, "w") as f:
                json.dump(self._schema_snapshot, f)
            logger.info("FAISS index saved to %s", path)

    def load(self, path: str) -> bool:
        """Load FAISS index from disk."""
        index_file = os.path.join(path, "index.faiss")
        schema_file = os.path.join(path, "schema_snapshot.json")
        if not os.path.exists(index_file):
            return False
        try:
            embeddings = get_embedding_model()
            self._store = FAISS.load_local(
                path, embeddings, allow_dangerous_deserialization=True
            )
            if os.path.exists(schema_file):
                with open(schema_file) as f:
                    self._schema_snapshot = json.load(f)
                self._total_tables = len(self._schema_snapshot.get("tables", {}))
            logger.info("FAISS index loaded from %s", path)
            return True
        except Exception as e:
            logger.warning("Failed to load FAISS index: %s", e)
            return False


# Singleton instance
_vector_store = SchemaVectorStore()


def get_vector_store() -> SchemaVectorStore:
    return _vector_store
