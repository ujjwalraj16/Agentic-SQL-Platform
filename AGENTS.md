# 🤖 DataSphere Agent Architecture

DataSphere implements a strict **multi-agent workflow** using **LangGraph**. Rather than relying on a single large LLM call to handle text-to-SQL (which often hallucinates), the system delegates responsibilities to three highly specialized agents.

## 1. Planner Agent (`planner.py`)
**Role:** The architect and intent parser.
- **Responsibility:** Receives the raw user input and formulates a structured execution plan.
- **Abilities:**
  - Determines if a query is asking for data retrieval, analytics, or just a generic conversation.
  - Detects ambiguity (e.g., "Show me sales" -> "Do you mean total revenue, or count of orders?").
  - Identifies which generic tables or entities the user is referring to.
- **Constraints:** Does not write SQL. Does not execute code. Output is strictly formatted JSON.

## 2. Schema Retrieval & Vector Store (`vector_store.py`)
*(Deterministic Tooling, not an LLM Agent)*
- Large databases have schemas too large to fit in an LLM context window.
- The system embeds all Table DDLs and column samples into a **FAISS** vector store using `sentence-transformers` (`all-MiniLM-L6-v2`).
- Based on the Planner's output, it performs a similarity search to fetch only the exact tables required to fulfill the user's intent.

## 3. SQL Generation Agent (`sql_agent.py`)
**Role:** The code generator.
- **Responsibility:** Translates the Planner's intent and the retrieved FAISS schema context into a highly optimized, dialect-specific SQL query.
- **Abilities:**
  - Understands primary/foreign key relationships provided in the schema context.
  - Can construct complex JOINs, Window Functions, and CTEs.
- **Self-Correction Loop:** If the `sql_executor` encounters a database error (e.g., "Column X does not exist"), the error is fed *back* to the SQL Agent. The agent is instructed to fix the syntax error and try again, up to a maximum of 3 times.

## 4. Analytics Agent (`analytics.py`)
**Role:** The data interpreter.
- **Responsibility:** Receives the raw JSON payload resulting from the successful SQL execution, and translates those numbers back into human-readable business insights.
- **Abilities:**
  - Identifies anomalies (e.g., "Revenue dropped 28% in Q2").
  - Summarizes the output without exposing the user to raw database JSON.
  - Determines if the data is a single scalar value, a time-series trend, or a comparative distribution.
- **Constraints:** Never executes SQL. Only operates on the `execution.rows` data provided to it by the LangGraph state.

## Tooling & Validation
The agents are supported by strict, deterministic Python logic:
- **SQL Validator:** Hardcoded regex and AST parsing to block DML/DDL commands.
- **Visualization Selector:** Heuristic-based logic that chooses the correct Recharts component (Bar, Line, Pie, or Table) based on the column data types returned by the query.
