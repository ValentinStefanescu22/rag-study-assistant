# HTTP API. Run with: uv run fastapi dev app/main.py

from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from fastapi import FastAPI, HTTPException, Query, UploadFile
from pypdf.errors import PdfReadError

from app import db, retrieve
from app.ingest import ingest_pdf

MAX_UPLOAD_BYTES = 50 * 1024 * 1024
OLLAMA_DOWN = "Embedding model unavailable. Is Ollama running?"


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_schema()  # runs once when the server starts
    yield


app = FastAPI(title="RAG Study Assistant", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


# Plain `def` (not `async def`): this does slow blocking work (PDF parsing, HTTP to Ollama, DB),
# so FastAPI runs it in a worker thread and the server stays responsive.
@app.post("/documents", status_code=201)
def upload_document(file: UploadFile):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported.")
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "PDF is larger than 50 MB.")
    try:
        return ingest_pdf(file.filename, data)
    except (PdfReadError, ValueError) as e:
        raise HTTPException(400, f"Could not read PDF: {e}")
    except httpx.HTTPError as e:
        raise HTTPException(503, f"{OLLAMA_DOWN} ({e})")


@app.get("/documents")
def list_documents():
    return db.list_documents()


# Retrieval only, no LLM: shows which chunks a question finds and how similar they are.
# FastAPI validates the query parameters and returns 422 if they're out of range.
@app.get("/search")
def search(
    q: Annotated[str, Query(min_length=1, max_length=1000)],
    k: Annotated[int, Query(ge=1, le=20)] = 5,
):
    try:
        return retrieve.search(q, k)
    except httpx.HTTPError as e:
        raise HTTPException(503, f"{OLLAMA_DOWN} ({e})")
