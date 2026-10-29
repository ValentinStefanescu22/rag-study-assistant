# RAG Study Assistant

Upload lecture PDFs, ask questions, get answers that cite the exact file and page.
Everything runs locally: FastAPI + PostgreSQL/pgvector + Ollama.

## Run it (current state: Phase 2, ingestion + retrieval)

Prerequisites: Docker Desktop, [uv](https://docs.astral.sh/uv/), [Ollama](https://ollama.com) running natively.

```bash
ollama pull nomic-embed-text          # the embedding model
docker compose up -d db               # Postgres + pgvector on localhost:5433
cd backend && uv run fastapi dev app/main.py   # API on http://localhost:8000
```

Open http://localhost:8000/docs to try the endpoints in the browser.

Tests: `cd backend && uv run pytest`

Concepts behind each step: [docs/learning-notes.md](docs/learning-notes.md).
