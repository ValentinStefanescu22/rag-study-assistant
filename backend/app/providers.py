# Calls to the models. Phase 3 adds the chat model here.

import httpx

from app.config import EMBED_MODEL, OLLAMA_URL

# nomic-embed-text was trained with these task prefixes. They belong to the model,
# so if you switch embedding models, check its model card and change them here.
DOC_PREFIX = "search_document: "
QUERY_PREFIX = "search_query: "


# Turn each text into a vector (a list of 768 floats) with the Ollama embedding model.
def _embed(texts: list[str]) -> list[list[float]]:
    response = httpx.post(
        f"{OLLAMA_URL}/api/embed",
        json={"model": EMBED_MODEL, "input": texts},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["embeddings"]


# Used at upload time, for chunks of a PDF.
def embed_documents(texts: list[str]) -> list[list[float]]:
    return _embed([DOC_PREFIX + text for text in texts])


# Used at search time, for the user's question.
def embed_query(text: str) -> list[float]:
    return _embed([QUERY_PREFIX + text])[0]
