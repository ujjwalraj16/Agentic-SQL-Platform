"""
tools/visualization.py – Automatic visualization selector (deterministic tool).

Inspects the result columns and data to determine the best chart type.
Returns a VisualizationConfig that the frontend can render with Recharts.

Rules:
- 1 string + 1 number column  → Bar chart
- 1 datetime + 1 number       → Line chart
- 2 number columns            → Scatter plot
- 1 column (category counts)  → Donut/Pie
- Multiple number columns     → Grouped bar or multi-line
- Very many rows              → Table (no chart)
"""

from __future__ import annotations
import logging
from typing import Any, Optional
import re

logger = logging.getLogger(__name__)

DATE_PATTERNS = [
    r"^\d{4}-\d{2}-\d{2}",    # ISO date
    r"^\d{4}-\d{2}$",          # Year-month
    r"^\d{4}$",                # Year only
    r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)",  # Month name
    r"^Q[1-4]\s+\d{4}",       # Quarter
]

NUMERIC_TYPES = {"int", "integer", "float", "double", "decimal", "numeric", "real", "bigint", "smallint"}
DATE_COLUMN_HINTS = {"date", "month", "year", "week", "quarter", "period", "time", "day"}
CATEGORY_COLUMN_HINTS = {"name", "category", "type", "status", "product", "customer", "department", "region"}


def determine_visualization(
    columns: list[str],
    rows: list[list[Any]],
    col_types: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    Determine the best visualization for the given result set.
    Returns a dict matching VisualizationConfig shape.
    """
    if not columns or not rows:
        return _table_fallback(columns, rows)

    n_cols = len(columns)
    n_rows = len(rows)

    # Too many rows for a chart → table
    if n_rows > 500:
        return _table_fallback(columns, rows)

    # Classify each column
    col_classes = _classify_columns(columns, rows, col_types)
    date_cols = [c for c, cls in col_classes.items() if cls == "date"]
    num_cols = [c for c, cls in col_classes.items() if cls == "numeric"]
    cat_cols = [c for c, cls in col_classes.items() if cls == "categorical"]

    chart_data = _rows_to_dicts(columns, rows)

    # ── Decision tree ─────────────────────────────────────────────────────────

    # Time series: date + ≥1 numeric
    if date_cols and num_cols:
        x = date_cols[0]
        y_cols = num_cols[:3]  # max 3 lines
        return {
            "chart_type": "line",
            "x_axis": x,
            "y_axis": y_cols[0],
            "y_axes": y_cols,
            "title": f"{', '.join(y_cols)} over {x}",
            "data": chart_data,
            "color_scheme": "indigo",
        }

    # 1 category + 1 numeric → bar
    if cat_cols and len(num_cols) == 1:
        x = cat_cols[0]
        y = num_cols[0]
        # Pie/donut for small datasets with one category
        if n_rows <= 8 and n_cols == 2:
            return {
                "chart_type": "pie",
                "x_axis": x,
                "y_axis": y,
                "y_axes": [y],
                "title": f"{y} by {x}",
                "data": chart_data,
                "color_scheme": "rainbow",
            }
        return {
            "chart_type": "bar",
            "x_axis": x,
            "y_axis": y,
            "y_axes": [y],
            "title": f"{y} by {x}",
            "data": chart_data,
            "color_scheme": "blue",
        }

    # 1 category + multiple numerics → grouped bar
    if cat_cols and len(num_cols) > 1:
        x = cat_cols[0]
        y_cols = num_cols[:4]
        return {
            "chart_type": "bar",
            "x_axis": x,
            "y_axis": y_cols[0],
            "y_axes": y_cols,
            "title": f"{', '.join(y_cols)} by {x}",
            "data": chart_data,
            "color_scheme": "purple",
        }

    # 2 numeric → scatter
    if len(num_cols) >= 2 and not cat_cols:
        return {
            "chart_type": "scatter",
            "x_axis": num_cols[0],
            "y_axis": num_cols[1],
            "y_axes": [num_cols[1]],
            "title": f"{num_cols[1]} vs {num_cols[0]}",
            "data": chart_data,
            "color_scheme": "green",
        }

    # 1 numeric only → histogram
    if len(num_cols) == 1 and not cat_cols:
        return {
            "chart_type": "histogram",
            "x_axis": num_cols[0],
            "y_axis": "count",
            "y_axes": [num_cols[0]],
            "title": f"Distribution of {num_cols[0]}",
            "data": chart_data,
            "color_scheme": "orange",
        }

    return _table_fallback(columns, rows)


def _table_fallback(columns: list[str], rows: list[list[Any]]) -> dict[str, Any]:
    return {
        "chart_type": "table",
        "x_axis": None,
        "y_axis": None,
        "y_axes": [],
        "title": "Query Results",
        "data": _rows_to_dicts(columns, rows),
        "color_scheme": "gray",
    }


def _rows_to_dicts(columns: list[str], rows: list[list[Any]]) -> list[dict[str, Any]]:
    return [dict(zip(columns, row)) for row in rows]


def _classify_columns(
    columns: list[str],
    rows: list[list[Any]],
    col_types: Optional[list[str]] = None,
) -> dict[str, str]:
    """Classify each column as 'date', 'numeric', or 'categorical'."""
    result: dict[str, str] = {}

    for i, col in enumerate(columns):
        col_lower = col.lower()

        # Hint from column name
        if any(hint in col_lower for hint in DATE_COLUMN_HINTS):
            result[col] = "date"
            continue

        # Check sample values
        sample_vals = [row[i] for row in rows[:20] if row[i] is not None]
        if not sample_vals:
            result[col] = "categorical"
            continue

        # Numeric?
        numeric_count = sum(1 for v in sample_vals if _is_numeric(v))
        if numeric_count / len(sample_vals) > 0.8:
            result[col] = "numeric"
            continue

        # Date?
        date_count = sum(1 for v in sample_vals if _looks_like_date(str(v)))
        if date_count / len(sample_vals) > 0.7:
            result[col] = "date"
            continue

        result[col] = "categorical"

    return result


def _is_numeric(v: Any) -> bool:
    if isinstance(v, (int, float)):
        return True
    try:
        float(str(v))
        return True
    except (ValueError, TypeError):
        return False


def _looks_like_date(s: str) -> bool:
    for pat in DATE_PATTERNS:
        if re.match(pat, s.strip(), re.IGNORECASE):
            return True
    return False
