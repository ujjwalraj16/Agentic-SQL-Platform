"""
database/schema.py – Schema introspection: extracts tables, columns, PKs, FKs,
sample values, and row counts from any SQLAlchemy-supported database.
"""

from __future__ import annotations
import logging
from typing import Any
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Maximum sample values per column
MAX_SAMPLES = 5
# Maximum rows to sample for values
SAMPLE_QUERY_LIMIT = 100


def extract_full_schema(engine: Engine) -> dict[str, Any]:
    """
    Return a structured schema dictionary covering all tables.
    Shape:
    {
        "database": "<name>",
        "db_type": "<type>",
        "tables": {
            "<table>": {
                "columns": [...],
                "row_count": int,
                "relationships": [...]
            }
        }
    }
    """
    inspector = inspect(engine)
    db_type = engine.dialect.name
    tables: dict[str, Any] = {}

    for table_name in inspector.get_table_names():
        columns = []
        pk_cols = {c for c in inspector.get_pk_constraint(table_name).get("constrained_columns", [])}
        fk_map: dict[str, str] = {}

        for fk in inspector.get_foreign_keys(table_name):
            for local_col, ref_col in zip(
                fk["constrained_columns"], fk["referred_columns"]
            ):
                fk_map[local_col] = f"{fk['referred_table']}.{ref_col}"

        for col in inspector.get_columns(table_name):
            col_name = col["name"]
            col_type = str(col["type"])
            columns.append(
                {
                    "name": col_name,
                    "type": col_type,
                    "nullable": col.get("nullable", True),
                    "primary_key": col_name in pk_cols,
                    "foreign_key": fk_map.get(col_name),
                    "sample_values": [],
                }
            )

        # Row count
        row_count = 0
        try:
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM \"{table_name}\""))
                row_count = result.scalar() or 0
        except Exception as e:
            logger.debug("Could not get row count for %s: %s", table_name, e)

        # Sample values for string/text columns
        try:
            with engine.connect() as conn:
                sample_rows = conn.execute(
                    text(f"SELECT * FROM \"{table_name}\" LIMIT {SAMPLE_QUERY_LIMIT}")
                ).fetchall()
                for i, col_info in enumerate(columns):
                    distinct_vals: list[Any] = []
                    seen = set()
                    for row in sample_rows:
                        v = row[i]
                        if v is not None and str(v) not in seen:
                            seen.add(str(v))
                            distinct_vals.append(v)
                        if len(distinct_vals) >= MAX_SAMPLES:
                            break
                    col_info["sample_values"] = distinct_vals
        except Exception as e:
            logger.debug("Could not fetch samples for %s: %s", table_name, e)

        # Relationships from FK info
        relationships = [
            f"{table_name}.{col} → {target}"
            for col, target in fk_map.items()
        ]

        tables[table_name] = {
            "columns": columns,
            "row_count": row_count,
            "relationships": relationships,
        }

    return {
        "database": engine.url.database or str(engine.url),
        "db_type": db_type,
        "tables": tables,
    }


def schema_to_compact_text(schema: dict[str, Any], tables: list[str] | None = None) -> str:
    """
    Convert schema dict to a compact text representation suitable for LLM prompts.
    If `tables` is given, only include those tables.
    """
    lines = [f"Database: {schema['database']} ({schema['db_type']})\n"]
    selected = tables or list(schema["tables"].keys())

    for tbl in selected:
        if tbl not in schema["tables"]:
            continue
        info = schema["tables"][tbl]
        lines.append(f"Table: {tbl} ({info['row_count']:,} rows)")
        for col in info["columns"]:
            flags = []
            if col["primary_key"]:
                flags.append("PK")
            if col["foreign_key"]:
                flags.append(f"FK→{col['foreign_key']}")
            if not col["nullable"]:
                flags.append("NOT NULL")
            flag_str = f" [{', '.join(flags)}]" if flags else ""
            samples = col["sample_values"][:3]
            sample_str = f" e.g. {samples}" if samples else ""
            lines.append(f"  - {col['name']} {col['type']}{flag_str}{sample_str}")
        if info["relationships"]:
            lines.append(f"  Relationships: {'; '.join(info['relationships'])}")
        lines.append("")

    return "\n".join(lines)
