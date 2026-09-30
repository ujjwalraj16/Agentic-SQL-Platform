# 🤖 DataSphere: Agentic SQL Intelligence Platform

A production-quality full-stack application that lets you query any relational database using natural language, powered by **AI agents** orchestrated with **LangGraph**.

## Architecture

```
USER
  → Planner Agent        (understands intent, detects ambiguity)
  → Schema Retrieval     (FAISS — retrieves only relevant tables)
  → SQL Agent            (generates SQL, self-corrects on error)
  → SQL Validator        (deterministic security + syntax check)
  → SQL Executor         (read-only execution with row limits)
  → Analytics Agent      (insights, trends, statistics)
  → Visualization Tool   (automatic chart selection)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12+, FastAPI, LangGraph, LangChain |
| LLM | Ollama (local) or Gemini API |
| Database | SQLite (demo), PostgreSQL, MySQL via SQLAlchemy |
| Vector Store | FAISS + sentence-transformers |
| Frontend | React 18, Vite, Recharts |

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env: set LLM_PROVIDER, OLLAMA_MODEL, DATABASE_URL

# Generate the sample database (25k orders, 7 tables)
python generate_sample_db.py

# Start the API server
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### 3. Ollama Setup

```bash
# Pull the model
ollama pull qwen3:8b

# Verify it's running
ollama list
```

## Configuration

Copy `.env.example` to `backend/.env` and set:

```env
# LLM Provider
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen3:8b
OLLAMA_BASE_URL=http://localhost:11434

# Or use Gemini
# LLM_PROVIDER=gemini
# GEMINI_API_KEY=your_key_here

# Database
DATABASE_URL=sqlite:///./data/sample.db
```


## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/query` | Run natural language query |
| POST | `/api/database/connect` | Connect to a database |
| POST | `/api/database/test` | Test a connection |
| GET | `/api/schema` | Get full database schema |
| GET | `/api/history` | Get query history |
| GET | `/api/metrics` | Get evaluation metrics |
| POST | `/api/query/optimize` | Optimize a SQL query |

## Security

- **READ-ONLY mode** enforced by default
- `DROP`, `DELETE`, `UPDATE`, `INSERT`, `CREATE`, `TRUNCATE`, `ALTER` are blocked
- SQL injection patterns detected deterministically (not by LLM)
- Database passwords never logged
- API keys loaded from environment variables only

## Agent Details

### Planner Agent
- Understands user intent
- Identifies relevant tables, operations, filters
- Detects ambiguity and asks for clarification
- Outputs structured JSON plan (no chain-of-thought exposed)

### SQL Agent
- Generates schema-aware SQL from the plan
- Supports: JOINs, GROUP BY, HAVING, subqueries, window functions, date filters
- Self-corrects on database errors (max 3 attempts)
- Returns confidence score

### Analytics Agent
- Analyzes query results (not raw data)
- Generates concise business insights
- Does not hallucinate beyond available data
- Computes deterministic statistics (min, max, avg, % change) without LLM

```
