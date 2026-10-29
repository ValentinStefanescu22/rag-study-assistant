# Retrieval: question -> query embedding -> the k closest chunks.
# Phase 3's chat endpoint calls `search` to get the sources it puts in the prompt.

from app import db
from app.providers import embed_query


def search(question: str, k: int = 5) -> list[dict]:
    return db.search_chunks(embed_query(question), k)
