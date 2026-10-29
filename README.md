# RAG Study Assistant

Upload lecture PDFs, ask questions, get answers that cite the exact file and page.
If the answer isn't in your materials, it says so instead of guessing.
Everything runs locally and for free: Angular + FastAPI + PostgreSQL/pgvector + Ollama.

## Run it

Prerequisites: Docker Desktop and [Ollama](https://ollama.com) running natively
(on macOS, Docker can't use the GPU, so the models stay outside Docker).

```bash
ollama pull nomic-embed-text   # embedding model
ollama pull qwen2.5:7b         # chat model
cp .env.example .env           # optional settings (e.g. switch to Claude)
docker compose up --build
```

Open http://localhost:8080. The API docs are at http://localhost:8080/api/docs.

To answer with Claude instead of the local model, set `LLM_PROVIDER=claude` and
`ANTHROPIC_API_KEY` in `.env` (paid; embeddings stay on Ollama).

## Development

Hot-reloading backend and frontend, with only the database in Docker.
Needs [uv](https://docs.astral.sh/uv/) and Node 22.22+/24.15+/26+.

```bash
docker compose up -d db                          # Postgres + pgvector on localhost:5433
cd backend && uv run fastapi dev app/main.py     # API on http://localhost:8000
cd frontend && npm install && npm start          # app on http://localhost:4200 (second terminal)
```

Tests: `cd backend && uv run pytest` and `cd frontend && npx ng test --watch=false`.
CI runs both, plus `docker compose build`, on every push ([.github/workflows/ci.yml](.github/workflows/ci.yml)).

## How it works

Concepts behind each step, written up for interview prep: [docs/learning-notes.md](docs/learning-notes.md).
