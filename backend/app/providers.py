# Calls to the models: embeddings (always Ollama) and chat (Ollama or Claude).

from functools import cache

import anthropic
import httpx

from app.config import CHAT_MODEL, CLAUDE_MODEL, EMBED_MODEL, LLM_PROVIDER, OLLAMA_URL

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


def _ollama_chat(system: str, user: str) -> str:
    response = httpx.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": CHAT_MODEL,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "stream": False,
            # Low temperature = less creative, more faithful to the sources.
            # num_ctx: Ollama's default context is small and it silently cuts off longer prompts.
            "options": {"temperature": 0.1, "num_ctx": 8192},
        },
        timeout=300,  # a local 7B model can take a while on long answers
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


@cache  # one client for the whole app, created on first use
def _claude_client() -> anthropic.Anthropic:
    return anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment


def _claude_chat(system: str, user: str) -> str:
    # No temperature: current Claude models reject sampling parameters.
    # fallbacks="default": if a safety filter declines, the API retries on a fallback model.
    response = _claude_client().beta.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=16000,
        system=system,
        messages=[{"role": "user", "content": user}],
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )
    if response.stop_reason == "refusal":
        return "NOT_FOUND"  # treat a declined request like "no answer in the sources"
    # The response is a list of blocks (thinking, text, ...); we only want the text.
    return "".join(block.text for block in response.content if block.type == "text")


# The one switch: LLM_PROVIDER picks which function `chat` is.
# An unknown value raises KeyError at startup instead of on the first question.
chat = {"ollama": _ollama_chat, "claude": _claude_chat}[LLM_PROVIDER]
