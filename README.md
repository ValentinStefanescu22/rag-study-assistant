# RAG Study Assistant

Upload your lecture PDFs and ask questions about them. Every answer cites the file and page
it came from, and if your slides don't cover something, it says so instead of guessing.
Runs locally and for free with Angular, FastAPI, PostgreSQL/pgvector and Ollama.

## Run it

You need Docker Desktop and [Ollama](https://ollama.com).

```bash
ollama pull nomic-embed-text
ollama pull qwen2.5:7b
docker compose up --build
```

Open http://localhost:8080.

## Use it

- **Upload PDFs** in the sidebar.
- **Ask a question.** The yellow page flags in the answer open the PDF on that page.
- **Summarize** a lecture, or all of them, for a cited overview.

To use Claude instead of the local model, set `LLM_PROVIDER=claude` and `ANTHROPIC_API_KEY` in a `.env` file (see `.env.example`).

## What I learned

- **Chunking:** splitting documents into small pieces (here, one per slide) so search can find the exact part that answers a question.
- **Embeddings:** turning text into vectors so that text with similar meaning ends up close together.
- **Vector search and indexing:** finding the closest chunks by cosine similarity in pgvector, with an HNSW index for speed at scale.
- **Citations:** the model only cites source numbers, and the code maps them to the file and page, so a citation can't be made up.
- **Evaluation:** a fixed set of test questions that measures retrieval (hit@k, MRR) and answers, so changes are judged by numbers instead of guesses.
