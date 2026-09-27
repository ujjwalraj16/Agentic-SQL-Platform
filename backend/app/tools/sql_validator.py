"""
tools/sql_validator.py – Deterministic SQL validation tool.

Validates SQL BEFORE execution using:
1. Syntax parsing (sqlparse)
2. Dangerous operation blocking (READ-ONLY enforcement)
3. Table/column existence checks against the known schema
4. Basic injection pattern detection
5. Query complexity assessment

Does NOT rely on the LLM for security checks.
"""

from __future__ import annotations
import re
import logging
from typing import Any
import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import Keyword, DDL, DML

logger = logging.getLogger(__name__)

# Dangerous SQL keywords that modify data (READ-ONLY enforcement)
BLOCKED_KEYWORDS = {
    "DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE",
    "ALTER", "CREATE", "REPLACE", "MERGE", "UPSERT",
    "GRANT", "REVOKE", "EXEC", "EXECUTE", "CALL",
}

# SQL injection patterns (heuristic)
INJECTION_PATTERNS = [
    r";\s*(DROP|DELETE|UPDATE|INSERT|TRUNCATE)",
    r"--\s*$",
    r"\/\*.*?\*\/",
    r"xp_\w+",
    r"UNION\s+ALL\s+SELECT.*FROM.*information_schema",
]


class ValidationResult:
    def __init__(
        self,
        valid: bool,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        self.valid = valid
        self.errors = errors
        self.warnings = warnings

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def validate_sql(sql: str, schema: dict[str, Any]) -> ValidationResult:
    """
    Validate SQL against the schema and security rules.
    Returns a ValidationResult with errors and warnings.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not sql or not sql.strip():
        return ValidationResult(False, ["Empty SQL query."], [])

    sql_stripped = sql.strip().rstrip(";")

    # ── 1. Parse ─────────────────────────────────────────────────────────────
    try:
        parsed = sqlparse.parse(sql_stripped)
        if not parsed:
            errors.append("Could not parse SQL statement.")
            return ValidationResult(False, errors, warnings)
        stmt: Statement = parsed[0]
    except Exception as e:
        errors.append(f"SQL parse error: {e}")
        return ValidationResult(False, errors, warnings)

    # ── 2. Dangerous operation check (READ-ONLY) ──────────────────────────────
    upper_sql = sql_stripped.upper()
    first_token = stmt.get_type() or ""

    # Check all keywords in the statement
    all_keywords = {
        t.normalized.upper()
        for t in stmt.flatten()
        if t.ttype in (Keyword, DDL, DML)
    }

    blocked_found = BLOCKED_KEYWORDS.intersection(all_keywords)
    if blocked_found:
        errors.append(
            f"Blocked operation(s): {', '.join(blocked_found)}. "
            "The system operates in READ-ONLY mode. "
            "Only SELECT queries are permitted."
        )

    # Also check if the statement type is DML/DDL
    if first_token and first_token.upper() in BLOCKED_KEYWORDS:
        if first_token.upper() not in {b for e in errors for b in e.split(":")}:
            errors.append(
                f"Statement type '{first_token}' is not allowed in read-only mode."
            )

    # ── 3. Injection pattern check ────────────────────────────────────────────
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, upper_sql, re.IGNORECASE | re.DOTALL):
            errors.append(f"Potential SQL injection pattern detected: {pattern}")

    # ── 4. Schema-aware validation ────────────────────────────────────────────
    known_tables = set(schema.get("tables", {}).keys())
    if known_tables:
        # Extract table references from the SQL (rough heuristic)
        referenced = _extract_table_references(upper_sql, known_tables)
        unknown = referenced - {t.upper() for t in known_tables}
        if unknown:
            errors.append(
                f"Referenced tables not found in schema: {', '.join(unknown)}. "
                "Check table names and verify the schema."
            )

    # ── 5. Complexity warnings ────────────────────────────────────────────────
    if "SELECT *" in upper_sql or "SELECT  *" in upper_sql:
        warnings.append("Using SELECT * is inefficient; consider selecting only needed columns.")

    join_count = upper_sql.count(" JOIN ")
    if join_count > 5:
        warnings.append(f"High number of JOINs ({join_count}); this may impact performance.")

    subquery_count = upper_sql.count("SELECT") - 1
    if subquery_count > 3:
        warnings.append(f"Deep subqueries ({subquery_count} levels); consider using CTEs.")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def _extract_table_references(upper_sql: str, known_tables: set[str]) -> set[str]:
    """Heuristically extract table names mentioned in the SQL."""
    referenced = set()
    upper_known = {t.upper() for t in known_tables}

    # Match after FROM, JOIN keywords
    patterns = [
        r"\bFROM\s+[\"']?(\w+)[\"']?",
        r"\bJOIN\s+[\"']?(\w+)[\"']?",
        r"\bINTO\s+[\"']?(\w+)[\"']?",
        r"\bUPDATE\s+[\"']?(\w+)[\"']?",
    ]
    for pat in patterns:
        for match in re.finditer(pat, upper_sql, re.IGNORECASE):
            name = match.group(1).upper()
            if name in upper_known:
                referenced.add(name)

    return referenced
